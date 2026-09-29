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
    records = query.order_by(DataRecordModel.confidence_score.desc(), DataRecordModel.created_at.desc()).offset(skip).limit(limit).all()

    formatted_records = []
    for r in records:
        data = dict(r.data_json) if isinstance(r.data_json, dict) else {}
        if "work_modality" not in data or not data["work_modality"]:
            rtype = str(data.get("remote_type") or "").lower()
            loc = str(data.get("location") or "").lower()
            is_online = (rtype == "remote") or any(k in loc for k in ["remote", "online", "virtual", "wfh", "anywhere"])
            data["work_modality"] = "Online" if is_online else "Offline"
            if "modality_detail" not in data:
                data["modality_detail"] = "Online (Remote)" if is_online else ("Offline (Hybrid)" if rtype == "hybrid" else "Offline (On-site)")

        formatted_records.append({
            "id": r.id,
            "workflow_id": r.workflow_id,
            "entity_name": r.entity_name,
            "data": data,
            "confidence_score": r.confidence_score,
            "confidence_breakdown": r.confidence_breakdown,
            "human_review_required": r.human_review_required,
            "source_url": r.source_url,
            "source_title": r.source_title,
            "extracted_timestamp": r.extracted_timestamp,
            "raw_snippet": r.raw_snippet,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return {
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "records": formatted_records
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

    payload = dict(record.data_json) if isinstance(record.data_json, dict) else {}
    if "work_modality" not in payload or not payload["work_modality"]:
        rtype = str(payload.get("remote_type") or "").lower()
        loc = str(payload.get("location") or "").lower()
        is_online = (rtype == "remote") or any(k in loc for k in ["remote", "online", "virtual", "wfh", "anywhere"])
        payload["work_modality"] = "Online" if is_online else "Offline"
        if "modality_detail" not in payload:
            payload["modality_detail"] = "Online (Remote)" if is_online else ("Offline (Hybrid)" if rtype == "hybrid" else "Offline (On-site)")

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
        "payload": payload
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
