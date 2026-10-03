"""
Workflow Management and Execution Endpoints strictly matching SDD specifications.
"""
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from backend.app.db.database import get_db, SessionLocal
    from backend.app.db.models import WorkflowModel, DataRecordModel
    from backend.app.websocket.ws_manager import ws_manager
    from backend.app.services.export_service import export_service
    from backend.app.intelligence.query_planner import parse_job_query_to_spec, JobSearchSpecification
    from backend.app.intelligence.orchestrator import run_job_ingestion_pipeline
except (ImportError, ModuleNotFoundError):
    from ..db.database import get_db, SessionLocal
    from ..db.models import WorkflowModel, DataRecordModel
    from ..websocket.ws_manager import ws_manager
    from ..services.export_service import export_service
    from ..intelligence.query_planner import parse_job_query_to_spec, JobSearchSpecification
    from ..intelligence.orchestrator import run_job_ingestion_pipeline

try:
    from backend.ai_engine.workflow_graph import DataIntelligenceWorkflow
except (ImportError, ModuleNotFoundError):
    from ai_engine.workflow_graph import DataIntelligenceWorkflow

router = APIRouter(prefix="/workflows", tags=["Workflows"])

class CreateWorkflowRequest(BaseModel):
    prompt: str
    confidence_threshold: float = 80.0
    query_spec: Optional[dict] = None

class PlanRequirementsRequest(BaseModel):
    prompt: str

class WorkflowSummaryResponse(BaseModel):
    id: str
    prompt: str
    status: str
    target_schema: Optional[dict] = None
    parsed_spec: Optional[dict] = None
    confidence_threshold: float
    total_extracted: int
    total_deduplicated: int
    duplicates_pruned: int
    human_review_count: int
    created_at: str
    completed_at: Optional[str] = None

@router.post("/plan")
def plan_requirements(req: PlanRequirementsRequest):
    """
    AI Query Planner: Converts natural-language request into structured search specification.
    Allows user to preview and edit requirements before launching search.
    """
    spec = parse_job_query_to_spec(req.prompt)
    return {
        "status": "success",
        "prompt": req.prompt,
        "spec": spec.model_dump()
    }

async def run_workflow_background(workflow_id: str, prompt: str, confidence_threshold: float, query_spec: Optional[dict] = None):
    """
    Executes real-time job ingestion pipeline across permitted sources (Greenhouse, Lever, Ashby, Jobicy, Arbeitnow, LinkOut).
    Streams live progress events over WebSocket and persists canonical records.
    """
    db = SessionLocal()
    try:
        wf_model = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
        if not wf_model:
            return

        # Step 1: Use provided query_spec or generate from prompt
        if query_spec:
            spec_dict = query_spec
        else:
            spec = parse_job_query_to_spec(prompt)
            spec_dict = spec.model_dump()

        wf_model.parsed_spec = spec_dict
        db.commit()

        # Step 2: Telemetry event broadcaster for real-time UI updates
        async def telemetry_callback(event: dict):
            await ws_manager.broadcast_to_workflow(workflow_id, {
                "type": "WORKFLOW_STEP",
                "workflow_id": workflow_id,
                **event
            })

        # Step 3: Run the real source ingestion pipeline
        pipeline_result = await run_job_ingestion_pipeline(
            workflow_id=workflow_id,
            query_spec=spec_dict,
            confidence_threshold=confidence_threshold,
            event_callback=telemetry_callback
        )

        # Refresh workflow record from DB
        wf_model = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
        db_records = db.query(DataRecordModel).filter(DataRecordModel.workflow_id == workflow_id).all()

        # Generate automatic Dataset Exports (CSV & JSON)
        try:
            export_service.export_to_json(db_records, workflow_id)
            export_service.export_to_csv(db_records, workflow_id)
        except Exception as e:
            print(f"Export auto-generation notice: {e}")

        # Final WebSocket Broadcast
        await ws_manager.broadcast_to_workflow(workflow_id, {
            "type": "WORKFLOW_COMPLETED",
            "workflow_id": workflow_id,
            "status": "completed",
            "total_records": len(db_records),
            "human_review_count": wf_model.human_review_count if wf_model else 0
        })

    except Exception as e:
        db.rollback()
        wf_model = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
        if wf_model:
            wf_model.status = "failed"
            wf_model.execution_logs = (wf_model.execution_logs or []) + [{"node": "error", "message": str(e)}]
            db.commit()
        await ws_manager.broadcast_to_workflow(workflow_id, {
            "type": "WORKFLOW_FAILED",
            "workflow_id": workflow_id,
            "error": str(e)
        })
    finally:
        db.close()

@router.post("", response_model=WorkflowSummaryResponse)
async def create_workflow(
    req: CreateWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    workflow_id = f"wf_{uuid.uuid4().hex[:10]}"
    
    # Pre-parse spec if not supplied
    spec_dict = req.query_spec or parse_job_query_to_spec(req.prompt).model_dump()

    wf = WorkflowModel(
        id=workflow_id,
        prompt=req.prompt,
        status="running",
        confidence_threshold=req.confidence_threshold,
        parsed_spec=spec_dict,
        created_at=datetime.now(timezone.utc)
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)

    # Launch background job ingestion task
    background_tasks.add_task(
        run_workflow_background,
        workflow_id=workflow_id,
        prompt=req.prompt,
        confidence_threshold=req.confidence_threshold,
        query_spec=spec_dict
    )

    return WorkflowSummaryResponse(
        id=wf.id,
        prompt=wf.prompt,
        status=wf.status,
        target_schema=wf.target_schema,
        parsed_spec=wf.parsed_spec,
        confidence_threshold=wf.confidence_threshold,
        total_extracted=0,
        total_deduplicated=0,
        duplicates_pruned=0,
        human_review_count=0,
        created_at=wf.created_at.isoformat()
    )

@router.get("", response_model=List[WorkflowSummaryResponse])
def list_workflows(limit: int = 20, db: Session = Depends(get_db)):
    wfs = db.query(WorkflowModel).order_by(WorkflowModel.created_at.desc()).limit(limit).all()
    res = []
    for w in wfs:
        res.append(WorkflowSummaryResponse(
            id=w.id,
            prompt=w.prompt,
            status=w.status,
            target_schema=w.target_schema,
            confidence_threshold=w.confidence_threshold,
            total_extracted=w.total_extracted,
            total_deduplicated=w.total_deduplicated,
            duplicates_pruned=w.duplicates_pruned,
            human_review_count=w.human_review_count,
            created_at=w.created_at.isoformat() if w.created_at else "",
            completed_at=w.completed_at.isoformat() if w.completed_at else None
        ))
    return res

@router.get("/{workflow_id}")
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    records = db.query(DataRecordModel).filter(DataRecordModel.workflow_id == workflow_id).all()

    return {
        "workflow": {
            "id": wf.id,
            "prompt": wf.prompt,
            "status": wf.status,
            "target_schema": wf.target_schema,
            "confidence_threshold": wf.confidence_threshold,
            "total_extracted": wf.total_extracted,
            "total_deduplicated": wf.total_deduplicated,
            "duplicates_pruned": wf.duplicates_pruned,
            "human_review_count": wf.human_review_count,
            "execution_logs": wf.execution_logs,
            "created_at": wf.created_at.isoformat() if wf.created_at else None,
            "completed_at": wf.completed_at.isoformat() if wf.completed_at else None
        },
        "records_count": len(records)
    }

@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    db.delete(wf)
    db.commit()
    return {"status": "deleted", "workflow_id": workflow_id}
