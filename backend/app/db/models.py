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
    parsed_spec = Column(JSON, nullable=True)  # Structured search specification from AI query planner
    confidence_threshold = Column(Float, default=80.0)
    
    # Metrics
    total_extracted = Column(Integer, default=0)
    total_deduplicated = Column(Integer, default=0)
    duplicates_pruned = Column(Integer, default=0)
    human_review_count = Column(Integer, default=0)
    sources_searched = Column(JSON, default=list)
    
    # Audit & Logs
    execution_logs = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    records = relationship("DataRecordModel", back_populates="workflow", cascade="all, delete-orphan")
    jobs = relationship("JobModel", back_populates="workflow", cascade="all, delete-orphan")


class DataRecordModel(Base):
    __tablename__ = "data_records"

    id = Column(String(64), primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.id", ondelete="CASCADE"), index=True)
    entity_name = Column(String(128), default="JobOpening")
    
    # Extracted data payload (conforms to Canonical Job schema)
    data_json = Column(JSON, nullable=False)
    
    # Deterministic Confidence scoring (Jev / Match Score)
    confidence_score = Column(Float, nullable=False)
    confidence_breakdown = Column(JSON, default=dict)
    human_review_required = Column(Boolean, default=False)
    
    # Source provenance & Lineage
    source_url = Column(Text, nullable=False)
    source_title = Column(Text, nullable=True)
    extracted_timestamp = Column(String(64), nullable=True)
    raw_snippet = Column(Text, nullable=True)
    deduplication_hash = Column(String(64), index=True)
    
    created_at = Column(DateTime, default=utc_now)

    workflow = relationship("WorkflowModel", back_populates="records")


class JobModel(Base):
    """
    Canonical Job Model strictly satisfying EDITH specifications.
    """
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.id", ondelete="SET NULL"), index=True, nullable=True)
    
    # Source & Application
    source = Column(String(64), nullable=False, index=True)  # greenhouse, lever, ashby, jobicy, etc.
    source_job_id = Column(String(128), nullable=True, index=True)
    source_url = Column(Text, nullable=False)
    apply_url = Column(Text, nullable=False)
    
    # Role & Organization
    title = Column(String(256), nullable=False, index=True)
    company = Column(String(256), nullable=False, index=True)
    company_url = Column(Text, nullable=True)
    company_domain = Column(String(128), nullable=True, index=True)
    
    # Descriptions & Requirements
    description = Column(Text, nullable=True)
    requirements = Column(JSON, default=list)
    responsibilities = Column(JSON, default=list)
    skills = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    
    # Location & Remote
    location = Column(String(256), nullable=True, index=True)
    city = Column(String(128), nullable=True, index=True)
    state = Column(String(128), nullable=True)
    country = Column(String(64), default="India", index=True)
    remote_type = Column(String(32), default="on-site", index=True)  # remote, hybrid, on-site
    
    # Employment & Experience
    employment_type = Column(String(64), default="full-time", index=True)  # full-time, internship, contract
    experience_min = Column(Float, nullable=True)
    experience_max = Column(Float, nullable=True)
    
    # Compensation
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(16), default="INR")
    salary_period = Column(String(16), default="year")
    
    # Qualifications
    education = Column(String(256), nullable=True)
    
    # Timestamps & Freshness
    date_posted = Column(String(64), nullable=True)
    date_updated = Column(String(64), nullable=True)
    first_seen_at = Column(DateTime, default=utc_now)
    last_seen_at = Column(DateTime, default=utc_now)
    
    # Status & Verification
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=True)
    source_timestamp = Column(String(64), nullable=True)
    raw_content_hash = Column(String(64), index=True)
    
    # EDITH Match Scoring & Explainability (0-100)
    match_score = Column(Float, default=0.0)
    score_breakdown = Column(JSON, default=dict)
    match_reasons = Column(JSON, default=list)  # ["✓ Python", "✓ Bangalore/Remote"]
    potential_gaps = Column(JSON, default=list)  # ["⚠ AWS mentioned", "⚠ Salary not disclosed"]
    
    # Quality & Risk Signals
    freshness_score = Column(Float, default=100.0)
    source_confidence = Column(Float, default=95.0)
    listing_quality_score = Column(Float, default=90.0)
    risk_signals = Column(JSON, default=list)
    
    # Canonical Multi-Source Merging
    sources = Column(JSON, default=list)  # ["greenhouse", "company-careers"]
    provenance = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    workflow = relationship("WorkflowModel", back_populates="jobs")


class UserProfileModel(Base):
    """
    User Profile for Job Seekers (Optional).
    Enables personalized Profile Match scoring.
    """
    __tablename__ = "user_profiles"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=True)
    email = Column(String(128), nullable=True, unique=True)
    
    skills = Column(JSON, default=list)
    experience_years = Column(Float, default=0.0)
    education = Column(String(256), nullable=True)
    
    preferred_roles = Column(JSON, default=list)
    preferred_locations = Column(JSON, default=list)
    remote_preference = Column(Boolean, default=True)
    salary_expectation = Column(Float, nullable=True)
    employment_preferences = Column(JSON, default=list)
    
    industries = Column(JSON, default=list)
    preferred_companies = Column(JSON, default=list)
    excluded_companies = Column(JSON, default=list)
    notice_period_days = Column(Integer, default=0)
    
    portfolio_url = Column(Text, nullable=True)
    github_url = Column(Text, nullable=True)
    linkedin_url = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class JobSourceModel(Base):
    """
    Source Policy Registry Persistence.
    """
    __tablename__ = "job_sources"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    domain = Column(String(128), nullable=False)
    access_method = Column(String(64), nullable=False)  # PUBLIC_API, PUBLIC_FEED, PUBLIC_CAREER_PAGE, AUTHORIZED_API, USER_PROVIDED_URL, LINK_OUT_ONLY
    permission_status = Column(String(64), default="PERMITTED")
    robots_policy = Column(Text, nullable=True)
    rate_limit = Column(String(64), default="60/min")
    parser = Column(String(64), nullable=False)
    last_checked = Column(DateTime, default=utc_now)
    status = Column(String(32), default="ONLINE")  # ONLINE, LINK_OUT_ONLY, DEGRADED, UNAVAILABLE
    latency_ms = Column(Integer, default=0)
    jobs_discovered = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)


class SavedJobModel(Base):
    """
    User Bookmarked / Saved Jobs.
    """
    __tablename__ = "saved_jobs"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), nullable=True, index=True)
    job_id = Column(String(64), ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    notes = Column(Text, nullable=True)
    status = Column(String(32), default="saved")  # saved, applied, interviewing, rejected, offered
    created_at = Column(DateTime, default=utc_now)
