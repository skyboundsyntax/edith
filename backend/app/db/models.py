"""
SQLAlchemy Data Models strictly matching SDD specifications.
Tables:
- Workflows: tracks workflow history, status, target_schema, metrics, logs, origin prompts.
- DataRecords: stores extracted JSON payloads, Jev confidence scores, origin URL metadata, timestamps, and raw snippet.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class WorkflowModel(Base):
    __tablename__ = "workflows"

    id = Column(String(64), primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String(32), default="pending")  # pending, running, completed, failed
    target_schema = Column(JSON, nullable=True)
    confidence_threshold = Column(Float, default=80.0)
    
    # Metrics
    total_extracted = Column(Integer, default=0)
    total_deduplicated = Column(Integer, default=0)
    duplicates_pruned = Column(Integer, default=0)
    human_review_count = Column(Integer, default=0)
    
    # Audit & Logs
    execution_logs = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    records = relationship("DataRecordModel", back_populates="workflow", cascade="all, delete-orphan")

class DataRecordModel(Base):
    __tablename__ = "data_records"

    id = Column(String(64), primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.id", ondelete="CASCADE"), index=True)
    entity_name = Column(String(128), default="Record")
    
    # Extracted data payload
    data_json = Column(JSON, nullable=False)
    
    # Deterministic Confidence scoring (Jev)
    confidence_score = Column(Float, nullable=False)
    confidence_breakdown = Column(JSON, default=dict)
    human_review_required = Column(Boolean, default=False)
    
    # Source provenance & Lineage (SDD Section 3)
    source_url = Column(Text, nullable=False)
    source_title = Column(Text, nullable=True)
    extracted_timestamp = Column(String(64), nullable=True)
    raw_snippet = Column(Text, nullable=True)
    deduplication_hash = Column(String(64), index=True)
    
    created_at = Column(DateTime, default=utc_now)

    workflow = relationship("WorkflowModel", back_populates="records")
