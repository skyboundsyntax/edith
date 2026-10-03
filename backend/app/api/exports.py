"""
Dataset Export Endpoints (CSV / JSON) strictly matching SDD specifications.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from backend.app.db.database import get_db
    from backend.app.db.models import DataRecordModel
    from backend.app.services.export_service import export_service
except (ImportError, ModuleNotFoundError):
    from ..db.database import get_db
    from ..db.models import DataRecordModel
    from ..services.export_service import export_service

router = APIRouter(prefix="/export", tags=["Export"])

class ExportRequest(BaseModel):
    workflow_id: Optional[str] = None
    format: str = "json"  # json or csv
    min_confidence: Optional[float] = None

@router.post("")
def trigger_export(req: ExportRequest, db: Session = Depends(get_db)):
    query = db.query(DataRecordModel)
    if req.workflow_id:
        query = query.filter(DataRecordModel.workflow_id == req.workflow_id)
    if req.min_confidence is not None:
        query = query.filter(DataRecordModel.confidence_score >= req.min_confidence)

    records = query.all()
    wf_id = req.workflow_id or "global"

    if req.format.lower() == "csv":
        result = export_service.export_to_csv(records, wf_id)
    else:
        result = export_service.export_to_json(records, wf_id)

    return {
        "status": "success",
        "format": result["format"],
        "filename": result["filename"],
        "record_count": result["record_count"],
        "download_url": result["download_url"]
    }

@router.get("/download")
def download_file(
    format: str = "json",
    workflow_id: Optional[str] = None,
    min_confidence: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(DataRecordModel)
    if workflow_id:
        query = query.filter(DataRecordModel.workflow_id == workflow_id)
    if min_confidence is not None:
        query = query.filter(DataRecordModel.confidence_score >= min_confidence)

    records = query.all()
    wf_id = workflow_id or "global"

    if format.lower() == "csv":
        result = export_service.export_to_csv(records, wf_id)
        media_type = "text/csv"
    else:
        result = export_service.export_to_json(records, wf_id)
        media_type = "application/json"

    return Response(
        content=result["raw_content"],
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )
