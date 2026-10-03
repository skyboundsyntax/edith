"""
FastAPI Main Application Entry Point for AI Data Intelligence Platform.
Strictly adheres to SDD specifications.
"""
import os
import sys
from pathlib import Path

# Add root directory and backend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
for _p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
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
from backend.app.api.sources import router as sources_router
from backend.app.api.profile import router as profile_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Agent for Deterministic, Source-Backed Job Intelligence (EDITH Platform)"
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
app.include_router(sources_router, prefix=settings.API_PREFIX)
app.include_router(profile_router, prefix=settings.API_PREFIX)

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
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(content="""<!doctype html>
<html lang="en" style="background:#070b14;color:#f8fafc;font-family:'Inter',system-ui,sans-serif;">
<head>
  <meta charset="utf-8">
  <title>EDITH | Launching Dashboard...</title>
  <meta http-equiv="refresh" content="1; url=http://localhost:5173">
  <style>
    body { background: #070b14; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
    .card { background: #0d1527; border: 1px solid rgba(14,165,233,0.3); border-radius: 16px; padding: 2.5rem; text-align: center; max-width: 520px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .btn { display: inline-block; background: #0ea5e9; color: #fff; text-decoration: none; padding: 0.85rem 1.75rem; border-radius: 8px; font-weight: 600; margin-top: 1.25rem; font-size: 0.95rem; }
    .btn:hover { background: #0284c7; }
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size:2.5rem;margin-bottom:0.5rem;">⚡</div>
    <h1 style="font-size:1.5rem;margin-bottom:0.5rem;color:#f8fafc;">EDITH Intelligence Active</h1>
    <p style="color:#94a3b8;font-size:0.95rem;margin-bottom:1rem;line-height:1.5;">Navigating to the Interactive Job Dashboard at <strong style="color:#38bdf8;">http://localhost:5173</strong>...</p>
    <a href="http://localhost:5173" class="btn">Open Interactive Dashboard</a>
    <div style="margin-top:1.5rem;font-size:0.8rem;color:#64748b;">
      Backend: <a href="/docs" style="color:#38bdf8;text-decoration:none;">API Swagger Docs (/docs)</a> • <a href="/api/workflows" style="color:#38bdf8;text-decoration:none;">Workflows API</a>
    </div>
  </div>
  <script>
    setTimeout(function() {
      window.location.href = "http://localhost:5173";
    }, 400);
  </script>
</body>
</html>""")

    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
