"""
Health, Environment and Diagnostics Endpoints strictly matching SDD specifications.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.db.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected" if db_ok else "unreachable",
        "ai_engine": {
            "langgraph": "active",
            "deterministic_jev": "active",
            "vector_deduplication": "active (scikit-learn tfidf cosine / Qdrant compatible)"
        }
    }
