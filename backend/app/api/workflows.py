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

from backend.app.db.database import get_db, SessionLocal
from backend.app.db.models import WorkflowModel, DataRecordModel
from backend.app.websocket.ws_manager import ws_manager
from backend.app.services.export_service import export_service
from ai_engine.workflow_graph import DataIntelligenceWorkflow

router = APIRouter(prefix="/workflows", tags=["Workflows"])

class CreateWorkflowRequest(BaseModel):
    prompt: str
    confidence_threshold: float = 80.0

class WorkflowSummaryResponse(BaseModel):
    id: str
    prompt: str
    status: str
    target_schema: Optional[dict] = None
    confidence_threshold: float
    total_extracted: int
    total_deduplicated: int
    duplicates_pruned: int
    human_review_count: int
    created_at: str
    completed_at: Optional[str] = None

async def run_workflow_background(workflow_id: str, prompt: str, confidence_threshold: float):
    """
    Executes LangGraph pipeline asynchronously with real-time telemetry streaming and DB persistence.
    """
    db = SessionLocal()
    try:
        wf_model = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
        if not wf_model:
            return

        pipeline = DataIntelligenceWorkflow(confidence_threshold=confidence_threshold)

        async def telemetry_callback(event: dict):
            # Broadcast over WebSocket
            await ws_manager.broadcast_to_workflow(workflow_id, {
                "type": "WORKFLOW_STEP",
                "workflow_id": workflow_id,
                **event
            })

        # Run the LangGraph state machine (SDD 2.1)
        final_state = await pipeline.run_pipeline(
            prompt=prompt,
            workflow_id=workflow_id,
            confidence_threshold=confidence_threshold,
            telemetry_callback=telemetry_callback
        )

        # Update Workflow DB entry
        wf_model.status = "completed"
        wf_model.target_schema = final_state.target_schema.model_dump() if final_state.target_schema else None
        wf_model.total_extracted = len(final_state.processed_data)
        wf_model.total_deduplicated = len(final_state.deduplicated_data)
        wf_model.duplicates_pruned = final_state.metrics.get("duplicates_pruned", 0)
        wf_model.human_review_count = final_state.metrics.get("human_review_count", 0)
        wf_model.execution_logs = final_state.execution_logs
        wf_model.completed_at = datetime.now(timezone.utc)

        # Persist extracted records (SDD 2.2)
        db_records = []
        for r in final_state.deduplicated_data:
            rec_model = DataRecordModel(
                id=r.record_id,
                workflow_id=workflow_id,
                entity_name=final_state.target_schema.entity_name if final_state.target_schema else "Record",
                data_json=r.data,
                confidence_score=r.confidence_score,
                confidence_breakdown=r.confidence_breakdown,
                human_review_required=r.human_review_required,
                source_url=r.source_url,
                source_title=r.source_title,
                extracted_timestamp=r.extracted_timestamp,
                raw_snippet=r.raw_snippet,
                deduplication_hash=r.deduplication_hash
            )
            db.add(rec_model)
            db_records.append(rec_model)

        db.commit()

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
            "human_review_count": wf_model.human_review_count,
            "schema": wf_model.target_schema
        })

    except Exception as e:
        db.rollback()
        wf_model = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
        if wf_model:
            wf_model.status = "failed"
            wf_model.execution_logs = wf_model.execution_logs + [{"node": "error", "message": str(e)}]
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
    wf = WorkflowModel(
        id=workflow_id,
        prompt=req.prompt,
        status="running",
        confidence_threshold=req.confidence_threshold,
        created_at=datetime.now(timezone.utc)
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)

    # Launch background LangGraph agent task
    background_tasks.add_task(
        run_workflow_background,
        workflow_id=workflow_id,
        prompt=req.prompt,
        confidence_threshold=req.confidence_threshold
    )

    return WorkflowSummaryResponse(
        id=wf.id,
        prompt=wf.prompt,
        status=wf.status,
        target_schema=wf.target_schema,
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
