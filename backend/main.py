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
    Seeds initial career intelligence and job scraping workflows if the database is fresh.
    Ensures the user can immediately experience the interactive multi-portal job board,
    direct application links, and Jev's Anti-Ghost Trust Meter.
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timezone

        wf_id = "wf_scraped_jobs_multiplatform"
        if db.query(WorkflowModel).filter(WorkflowModel.id == wf_id).count() == 0:
            wf = WorkflowModel(
                id=wf_id,
                prompt="Find active Full-Stack and Python Engineer job openings on LinkedIn, Naukri, and Indeed with salary, skills, and direct apply link",
                status="completed",
                target_schema={
                    "entity_name": "JobOpening",
                    "description": "Structured job posting from LinkedIn, Naukri, Indeed, or verified career portals",
                    "fields": [
                        {"name": "job_title", "type": "string", "description": "Official title of the open position", "required": True},
                        {"name": "company", "type": "string", "description": "Hiring company or organization", "required": True},
                        {"name": "location", "type": "string", "description": "City, Country, Remote, or Hybrid status", "required": True},
                        {"name": "experience_years", "type": "string", "description": "Required years of experience", "required": False},
                        {"name": "skills", "type": "list", "description": "Core technical competencies and tools required", "required": False},
                        {"name": "salary_range", "type": "string", "description": "Disclosed compensation package or CTC", "required": False},
                        {"name": "platform_source", "type": "string", "description": "Origin platform (LinkedIn, Naukri, Indeed, Career Site)", "required": True},
                        {"name": "apply_link", "type": "string", "description": "Direct application page or posting URL", "required": True}
                    ]
                },
                confidence_threshold=80.0,
                total_extracted=3,
                total_deduplicated=3,
                duplicates_pruned=1,
                human_review_count=0,
                execution_logs=[
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "intent_parser", "message": "Derived JobOpening schema for Full-Stack & Python roles with salary disclosure"},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "source_discovery", "message": "Multi-portal crawl executed across LinkedIn Jobs, Naukri.com, and Indeed"},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "data_extraction", "message": "Jev Trust Meter evaluated employer authenticity, direct apply integrity, and compensation transparency"},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "vector_deduplication", "message": "Vector similarity deduplicated 1 cross-board duplicate listing"},
                    {"timestamp": datetime.now(timezone.utc).isoformat(), "node": "human_review_evaluation", "message": "All postings verified >= 88.0% Jev Trust Score. Zero anti-ghost flags."}
                ],
                created_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            db.add(wf)

            sample_jobs = [
                {
                    "id": "rec_job_linkedin_01",
                    "data": {
                        "job_title": "Senior Full-Stack Engineer (Python / React)",
                        "company": "NexusCore AI Systems",
                        "location": "Bangalore / Remote",
                        "experience_years": "3-6 years",
                        "skills": ["Python", "FastAPI", "React 19", "PostgreSQL", "Docker"],
                        "salary_range": "₹28 - ₹42 LPA",
                        "platform_source": "LinkedIn",
                        "apply_link": "https://www.linkedin.com/jobs/view/senior-fullstack-engineer-3982019421"
                    },
                    "confidence": 94.6,
                    "breakdown": {"completeness": 100.0, "source_grounding": 95.0, "syntax_validity": 100.0, "information_density": 96.0},
                    "source_url": "https://www.linkedin.com/jobs/view/senior-fullstack-engineer-3982019421",
                    "source_title": "Senior Full-Stack Engineer at NexusCore AI Systems | LinkedIn",
                    "snippet": "NexusCore AI Systems is hiring a Senior Full-Stack Engineer in Bangalore / Remote. Requirements: 3-6 years with Python, FastAPI, React 19, Docker, and PostgreSQL. Disclosed CTC: ₹28 - ₹42 LPA. Direct application active."
                },
                {
                    "id": "rec_job_naukri_02",
                    "data": {
                        "job_title": "Lead Cloud & Backend Specialist",
                        "company": "CloudSystems Technologies",
                        "location": "Hyderabad / Hybrid",
                        "experience_years": "4-7 years",
                        "skills": ["Python", "AWS", "FastAPI", "Kubernetes", "Redis"],
                        "salary_range": "₹32 - ₹48 LPA",
                        "platform_source": "Naukri",
                        "apply_link": "https://www.naukri.com/job-listings-cloud-systems-bangalore-280924001928"
                    },
                    "confidence": 92.4,
                    "breakdown": {"completeness": 100.0, "source_grounding": 91.0, "syntax_validity": 100.0, "information_density": 94.0},
                    "source_url": "https://www.naukri.com/job-listings-cloud-systems-bangalore-280924001928",
                    "source_title": "Lead Cloud & Backend Specialist at CloudSystems | Naukri.com",
                    "snippet": "CloudSystems Technologies recruitment board on Naukri.com. Looking for Lead Backend Specialist (Python, AWS, Kubernetes). 4-7 years experience. Compensation package: ₹32 - ₹48 LPA. Verified recruiter posting."
                },
                {
                    "id": "rec_job_indeed_03",
                    "data": {
                        "job_title": "Software Development Engineer (Cloud Systems)",
                        "company": "Apex Cloud Systems",
                        "location": "Bangalore, India",
                        "experience_years": "2-5 years",
                        "skills": ["Python", "Go", "Vector DBs", "Docker", "REST APIs"],
                        "salary_range": "₹22 - ₹36 LPA",
                        "platform_source": "Indeed",
                        "apply_link": "https://www.indeed.com/viewjob?jk=8a92bc01829e120f"
                    },
                    "confidence": 89.8,
                    "breakdown": {"completeness": 100.0, "source_grounding": 88.0, "syntax_validity": 95.0, "information_density": 92.0},
                    "source_url": "https://www.indeed.com/viewjob?jk=8a92bc01829e120f",
                    "source_title": "Software Development Engineer at Apex Cloud Systems | Indeed",
                    "snippet": "Apex Cloud Systems on Indeed. Software Development Engineer (SDE II) specializing in Python, Go, and Vector DB retrieval architectures in Bangalore. CTC: ₹22 - ₹36 LPA. Verified employer badge."
                }
            ]

            for s in sample_jobs:
                rec = DataRecordModel(
                    id=s["id"],
                    workflow_id=wf_id,
                    entity_name="JobOpening",
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
