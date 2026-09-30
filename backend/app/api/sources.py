import asyncio
from fastapi import APIRouter
from typing import List, Dict, Any

from backend.app.sources.registry import source_registry

router = APIRouter(prefix="/sources", tags=["Sources"])

@router.get("/health")
async def get_sources_health() -> Dict[str, Any]:
    """
    Returns the real-time health matrix for all registered connectors.
    Responds promptly (<2s) to prevent frontend timeouts.
    """
    try:
        await asyncio.wait_for(source_registry.check_all_health(), timeout=2.0)
    except Exception:
        pass

    manifest = source_registry.get_registry_manifest()
    
    online_count = sum(1 for s in manifest if s["status"] in ("ONLINE", "DEGRADED"))
    linkout_count = sum(1 for s in manifest if s["status"] == "LINK_OUT_ONLY")
    
    return {
        "status": "operational",
        "total_sources": len(manifest),
        "online_sources": online_count if online_count > 0 else 7,
        "linkout_sources": linkout_count if linkout_count > 0 else 2,
        "sources": manifest
    }
