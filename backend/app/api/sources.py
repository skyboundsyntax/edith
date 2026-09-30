"""
Source Management and Health Endpoints.
Displays real-time status of all registered job connectors (Online vs Link-Out).
"""
from fastapi import APIRouter
from typing import List, Dict, Any

from backend.app.sources.registry import source_registry

router = APIRouter(prefix="/sources", tags=["Sources"])

@router.get("/health")
async def get_sources_health(force: bool = False) -> Dict[str, Any]:
    """
    Returns the real-time health matrix for all registered connectors.
    Instant non-blocking return with live probe support on force=True.
    """
    if force or not source_registry.last_health_check:
        await source_registry.check_all_health(force=force)
    manifest = source_registry.get_registry_manifest()
    
    online_count = sum(1 for s in manifest if s["status"] in ["ONLINE", "DEGRADED"] and s["access_method"] != "LINK_OUT_ONLY")
    linkout_count = sum(1 for s in manifest if s["status"] == "LINK_OUT_ONLY" or s["access_method"] == "LINK_OUT_ONLY")
    
    return {
        "status": "operational",
        "total_sources": len(manifest),
        "online_sources": online_count,
        "linkout_sources": linkout_count,
        "sources": manifest
    }
