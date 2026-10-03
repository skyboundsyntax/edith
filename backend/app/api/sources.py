"""
Source Management and Health Endpoints.
Displays real-time status of all registered job connectors (Online vs Link-Out).
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

try:
    from backend.app.sources.registry import source_registry
    from backend.app.services.firecrawl_service import firecrawl_service
except (ImportError, ModuleNotFoundError):
    from ..sources.registry import source_registry
    from ..services.firecrawl_service import firecrawl_service
try:
    from backend.ai_engine.jev_extractor import jev_extractor
except (ImportError, ModuleNotFoundError):
    from ai_engine.jev_extractor import jev_extractor

router = APIRouter(prefix="/sources", tags=["Sources"])

class ScrapeUrlRequest(BaseModel):
    url: str
    query: Optional[str] = "Software Engineer"
    extract_with_jev: bool = True

class FirecrawlSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

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

@router.post("/scrape")
async def scrape_url(req: ScrapeUrlRequest) -> Dict[str, Any]:
    """
    Scrapes any web job URL or career portal with Firecrawl (with local fallback).
    Extracts structured schema-typed fields and evaluates confidence using Jev.
    """
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="A valid URL is required for scraping")

    scrape_res = await firecrawl_service.scrape_url(req.url.strip())
    
    extracted_records = []
    if req.extract_with_jev and scrape_res.get("success"):
        extracted_records = jev_extractor.extract_from_firecrawl(scrape_res, query=req.query or "")

    return {
        "status": "success",
        "url": req.url,
        "title": scrape_res.get("title"),
        "provider": scrape_res.get("provider"),
        "latency_ms": scrape_res.get("latency_ms", 0),
        "markdown_length": len(scrape_res.get("markdown", "")),
        "raw_snippet": (scrape_res.get("text") or scrape_res.get("markdown") or "")[:450],
        "extracted_count": len(extracted_records),
        "records": extracted_records,
        "jev_audit": {
            "overall_score": extracted_records[0].get("confidence_score") if extracted_records else 0.0,
            "breakdown": extracted_records[0].get("confidence_breakdown") if extracted_records else {},
            "human_review_required": extracted_records[0].get("human_review_required", True) if extracted_records else True,
            "evaluator": "TypeSafe Jev Deterministic Engine"
        } if extracted_records else None
    }

@router.post("/firecrawl/search")
async def search_firecrawl(req: FirecrawlSearchRequest) -> Dict[str, Any]:
    """
    Searches web career boards using Firecrawl and extracts live vacancies via Jev.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Search query is required")

    docs = await firecrawl_service.search(req.query.strip(), limit=req.limit or 5)
    all_jobs = []
    for d in docs:
        extracted = jev_extractor.extract_from_firecrawl(d, query=req.query)
        all_jobs.extend(extracted)

    return {
        "status": "success",
        "query": req.query,
        "provider": "firecrawl",
        "raw_documents_found": len(docs),
        "jev_extracted_jobs": len(all_jobs),
        "jobs": all_jobs
    }

@router.get("/firecrawl/status")
async def get_firecrawl_status() -> Dict[str, Any]:
    """
    Returns Firecrawl API connectivity and credit usage status.
    """
    status_info = await firecrawl_service.health_check()
    return {
        "status": "success",
        "firecrawl": status_info
    }

