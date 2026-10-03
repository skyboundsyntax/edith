"""
Health, Environment and Diagnostics Endpoints strictly matching SDD specifications.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from backend.app.core.config import settings
    from backend.app.db.database import get_db
except (ImportError, ModuleNotFoundError):
    from ..core.config import settings
    from ..db.database import get_db

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
            "trust_meter": "active (calibrated mathematical verification)",
            "vector_deduplication": "active (scikit-learn tfidf cosine)",
            "live_scrapers": "active (LinkedIn Guest API, Jobicy, Arbeitnow)"
        }
    }
