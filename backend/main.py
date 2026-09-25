"""
FastAPI Main Application Entry Point for AI Data Intelligence Platform.
Strictly adheres to SDD specifications.
"""
import os
import sys
from pathlib import Path

# Add root directory to sys.path so backend and ai_engine can import each other seamlessly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.db.database import engine, Base, SessionLocal
from backend.app.db.models import WorkflowModel, DataRecordModel
from backend.app.websocket.ws_manager import ws_manager

from backend.app.api.workflows import router as workflows_router
from backend.app.api.datasets import router as datasets_router
from backend.app.api.exports import router as exports_router
from backend.app.api.health import router as health_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Agent for Deterministic, Source-Backed Data Intelligence (SDD Specification)"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local exports folder
exports_path = Path(settings.EXPORTS_DIR)
exports_path.mkdir(parents=True, exist_ok=True)
app.mount("/exports", StaticFiles(directory=str(exports_path)), name="exports")

# Include Routers
app.include_router(workflows_router, prefix=settings.API_PREFIX)
app.include_router(datasets_router, prefix=settings.API_PREFIX)
app.include_router(exports_router, prefix=settings.API_PREFIX)
app.include_router(health_router, prefix=settings.API_PREFIX)

# WebSocket Real-Time Telemetry Endpoints (SDD 2.2)
@app.websocket("/ws/workflows/{workflow_id}")
async def workflow_websocket_endpoint(websocket: WebSocket, workflow_id: str):
    await ws_manager.connect(websocket, workflow_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, workflow_id)

@app.websocket("/ws/live")
async def global_websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket, "global")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "global")

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }

def seed_initial_dynamic_data():
    """
    Seeds initial dynamic workflows if the database is fresh.
    Ensures the user can immediately experience the interactive dashboard,
    source traceability links, and deterministic Jev confidence scores.
    """
    db = SessionLocal()
    try:
        if db.query(WorkflowModel).count() == 0:
            from datetime import datetime, timezone
            
            wf_id = "wf_ai_engineers_blr"
            wf = WorkflowModel(
                id=wf_id,
                prompt="Find me AI and distributed systems engineers in Bangalore with LangGraph and PyTorch expertise",
                status="completed",
                target_schema={
                    "entity_name": "ProfessionalCandidate",
                    "description": "Structured candidate profile extracted from verified public sources",
                    "fields": [
                        {"name": "full_name", "type": "string", "description": "Candidate Name", "required": True},
                        {"name": "role_title", "type": "string", "description": "Specialization Title", "required": True},
                        {"name": "organization", "type": "string", "description": "Current Company", "required": True},
                        {"name": "location", "type": "string", "description": "City / Hub", "required": True},
                        {"name": "skills", "type": "list", "description": "Technical Skills", "required": True},
                        {"name": "experience_years", "type": "string", "description": "Experience", "required": False},
                        {"name": "profile_link", "type": "string", "description": "Verified Profile URL", "required": True}
                    ]
                },
                confidence_threshold=80.0,
                total_extracted=3,
                total_deduplicated=3,
                duplicates_pruned=0,
                human_review_count=0,
                execution_logs=[
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "intent_parser", "message": "Derived schema for ProfessionalCandidate"},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "source_discovery", "message": "Gathered verified Bangalore tech talent indices"},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "data_extraction", "message": "Extracted strictly typed entities with Jev deterministic scoring"},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "vector_deduplication", "message": "Evaluated cosine similarity matrix: 0 duplicates pruned"},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "human_review_evaluation", "message": "All records scored >= 85.0%. No human review required."}
                ],
                created_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            db.add(wf)

            sample_data = [
                {
                    "id": "rec_arjun_01",
                    "data": {
                        "full_name": "Arjun Sundaram",
                        "role_title": "Lead AI / ML Systems Engineer",
                        "organization": "HyperScale Labs",
                        "location": "Bangalore, India",
                        "skills": ["PyTorch", "Distributed Training", "CUDA", "LangGraph", "FastAPI"],
                        "experience_years": "7+ Years",
                        "profile_link": "https://linkedin.com/in/arjun-sundaram-ai"
                    },
                    "confidence": 94.2,
                    "breakdown": {"completeness": 100.0, "source_grounding": 92.5, "syntax_validity": 100.0, "information_density": 95.0},
                    "source_url": "https://linkedin.com/in/arjun-sundaram-ai",
                    "source_title": "Arjun Sundaram - Lead AI Engineer | Public Directory",
                    "snippet": "Lead AI/ML Systems Engineer at HyperScale Labs Bangalore. Specialized in distributed training clusters, CUDA kernels, LangGraph workflow orchestration, and high-throughput inference APIs."
                },
                {
                    "id": "rec_kavita_02",
                    "data": {
                        "full_name": "Dr. Kavita Narayanan",
                        "role_title": "Principal Generative AI Researcher",
                        "organization": "TensorVenture Research",
                        "location": "Bangalore, India",
                        "skills": ["LLM Pretraining", "RLHF", "Transformer Kernels", "vLLM"],
                        "experience_years": "9 Years",
                        "profile_link": "https://scholar.google.com/citations?user=kavita-narayanan"
                    },
                    "confidence": 96.8,
                    "breakdown": {"completeness": 100.0, "source_grounding": 96.0, "syntax_validity": 100.0, "information_density": 98.0},
                    "source_url": "https://scholar.google.com/citations?user=kavita-narayanan",
                    "source_title": "Dr. Kavita Narayanan - Citations & Research Profile",
                    "snippet": "Principal Researcher focusing on post-training alignment, deterministic guardrails, and efficient attention mechanisms in Bangalore AI research clusters."
                },
                {
                    "id": "rec_rohan_03",
                    "data": {
                        "full_name": "Rohan Deshmukh",
                        "role_title": "Senior AI Infrastructure Engineer",
                        "organization": "Apex Cloud Systems",
                        "location": "Bangalore, India",
                        "skills": ["Kubernetes", "Triton Inference Server", "Ray.io", "Python", "Go"],
                        "experience_years": "5 Years",
                        "profile_link": "https://github.com/rohan-deshmukh"
                    },
                    "confidence": 88.5,
                    "breakdown": {"completeness": 90.0, "source_grounding": 85.0, "syntax_validity": 100.0, "information_density": 92.0},
                    "source_url": "https://github.com/rohan-deshmukh",
                    "source_title": "Rohan Deshmukh (rohan-deshmukh) / Tech Repositories",
                    "snippet": "Senior Infrastructure engineer managing high-availability GPU orchestration clusters on Kubernetes with Ray and Triton in Bangalore."
                }
            ]

            for s in sample_data:
                rec = DataRecordModel(
                    id=s["id"],
                    workflow_id=wf_id,
                    entity_name="ProfessionalCandidate",
                    data_json=s["data"],
                    confidence_score=s["confidence"],
                    confidence_breakdown=s["breakdown"],
                    human_review_required=False,
                    source_url=s["source_url"],
                    source_title=s["source_title"],
                    extracted_timestamp=datetime.now(timezone.utc).isoformat(),
                    raw_snippet=s["snippet"],
                    deduplication_hash=f"hash_{s['id']}"
                )
                db.add(rec)

            db.commit()
    except Exception as e:
        print(f"Initial seed notice: {e}")
    finally:
        db.close()

seed_initial_dynamic_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
