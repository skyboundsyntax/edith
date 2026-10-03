"""
Workflow State Definition for the AI Data Intelligence Platform.
Implements the LangGraph state machine contract defined strictly in the SDD (Section 2.1).
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class SchemaField(BaseModel):
    name: str
    type: str = "string"  # string, int, float, list, boolean
    description: str = ""
    required: bool = True

class TargetSchemaDefinition(BaseModel):
    entity_name: str
    description: str
    fields: List[SchemaField]

class ExtractedRecord(BaseModel):
    record_id: str
    data: Dict[str, Any]
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    source_url: str
    source_title: Optional[str] = None
    extracted_timestamp: str
    raw_snippet: Optional[str] = None
    human_review_required: bool = False
    deduplication_hash: Optional[str] = None

class WorkflowState(BaseModel):
    workflow_id: str
    user_prompt: str
    current_node: str = "initialized"
    target_schema: Optional[TargetSchemaDefinition] = None
    pending_urls: List[str] = Field(default_factory=list)
    raw_documents: List[Dict[str, Any]] = Field(default_factory=list)
    processed_data: List[ExtractedRecord] = Field(default_factory=list)
    deduplicated_data: List[ExtractedRecord] = Field(default_factory=list)
    error_logs: List[str] = Field(default_factory=list)
    execution_logs: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    confidence_threshold: float = 80.0
    status: str = "pending"  # pending, running, completed, failed
