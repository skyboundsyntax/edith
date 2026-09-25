"""
Dataset Querying and Provenance Traceability Endpoints (SDD Section 3).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.db.database import get_db
from backend.app.db.models import DataRecordModel

router = APIRouter(prefix="/datasets", tags=["Datasets"])

class ReviewActionRequest(BaseModel):
    action: str  # approve, reject
    notes: Optional[str] = None

@router.get("")
def list_datasets(
    workflow_id: Optional[str] = None,
    min_confidence: Optional[float] = None,
    human_review_only: Optional[bool] = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(DataRecordModel)

    if workflow_id:
        query = query.filter(DataRecordModel.workflow_id == workflow_id)
    if min_confidence is not None:
        query = query.filter(DataRecordModel.confidence_score >= min_confidence)
    if human_review_only:
        query = query.filter(DataRecordModel.human_review_required == True)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                DataRecordModel.source_title.ilike(search_pattern),
                DataRecordModel.source_url.ilike(search_pattern),
                DataRecordModel.raw_snippet.ilike(search_pattern)
            )
        )

    total_count = query.count()
    records = query.order_by(DataRecordModel.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "records": [
            {
                "id": r.id,
                "workflow_id": r.workflow_id,
                "entity_name": r.entity_name,
                "data": r.data_json,
                "confidence_score": r.confidence_score,
                "confidence_breakdown": r.confidence_breakdown,
                "human_review_required": r.human_review_required,
                "source_url": r.source_url,
                "source_title": r.source_title,
                "extracted_timestamp": r.extracted_timestamp,
                "raw_snippet": r.raw_snippet,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    }

@router.get("/{record_id}/provenance")
def get_record_provenance(record_id: str, db: Session = Depends(get_db)):
    """
    Returns full source lineage and audit details for a specific extracted entity.
    Directly addresses SDD Section 3 (Data Lineage & Traceability).
    """
    record = db.query(DataRecordModel).filter(DataRecordModel.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return {
        "record_id": record.id,
        "workflow_id": record.workflow_id,
        "entity_name": record.entity_name,
        "source": {
            "url": record.source_url,
            "title": record.source_title,
            "captured_timestamp": record.extracted_timestamp,
            "raw_snippet": record.raw_snippet
        },
        "confidence_evaluation": {
            "overall_score": record.confidence_score,
            "breakdown": record.confidence_breakdown,
            "human_review_required": record.human_review_required,
            "evaluator": "TypeSafe Jev Deterministic Engine"
        },
        "deduplication_hash": record.deduplication_hash,
        "payload": record.data_json
    }

@router.post("/{record_id}/review")
def review_record(record_id: str, req: ReviewActionRequest, db: Session = Depends(get_db)):
    """
    Handles human review resolution for records below confidence threshold.
    """
    record = db.query(DataRecordModel).filter(DataRecordModel.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if req.action == "approve":
        record.human_review_required = False
        record.confidence_score = max(record.confidence_score, 85.0)
    elif req.action == "reject":
        db.delete(record)
        db.commit()
        return {"status": "record_deleted"}

    db.commit()
    return {"status": "updated", "record_id": record.id, "human_review_required": record.human_review_required}
