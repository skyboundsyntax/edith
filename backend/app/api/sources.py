"""
Source Management and Health Endpoints.
Displays real-time status of all registered job connectors (Online vs Link-Out).
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel
import hashlib

try:
    from backend.app.sources.registry import source_registry
    from backend.app.intelligence.query_planner import parse_job_query_to_spec
    from backend.app.intelligence.role_matcher import is_matching_role
    from backend.app.locations.india_locations import matches_location_preference
    from backend.app.services.firecrawl_service import (
        firecrawl_service,
        filter_job_listing_documents,
        is_job_listing_document,
    )
except (ImportError, ModuleNotFoundError):
    from ..sources.registry import source_registry
    from ..intelligence.query_planner import parse_job_query_to_spec
    from ..intelligence.role_matcher import is_matching_role
    from ..locations.india_locations import matches_location_preference
    from ..services.firecrawl_service import (
        firecrawl_service,
        filter_job_listing_documents,
        is_job_listing_document,
    )
try:
    from backend.ai_engine.jev_extractor import jev_extractor
except (ImportError, ModuleNotFoundError):
    from ai_engine.jev_extractor import jev_extractor
try:
    from backend.ai_engine.source_discovery import SourceDiscovery
except (ImportError, ModuleNotFoundError):
    from ai_engine.source_discovery import SourceDiscovery

router = APIRouter(prefix="/sources", tags=["Sources"])

class ScrapeUrlRequest(BaseModel):
    url: str
    query: Optional[str] = None
    extract_with_jev: bool = True
    mode: Literal["job", "data"] = "job"

class FirecrawlSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    mode: Literal["job", "data"] = "job"


def _to_live_job(source_document: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize a verified public-job-API result for the Firecrawl search UI."""
    metadata = source_document.get("metadata") or {}
    source_name = str(source_document.get("source") or "").strip()
    # SourceDiscovery's final directory link is a search shortcut, not an
    # individual posting.  Never render it as one.
    if source_name == "LinkedIn Directory":
        return None
    title = str(metadata.get("job_title") or "").strip()
    apply_url = str(metadata.get("apply_link") or source_document.get("url") or "").strip()
    if not title or not apply_url:
        return None

    company = str(metadata.get("company") or "").strip()
    record_key = f"{title}|{company}|{apply_url}".encode("utf-8")
    record_id = hashlib.sha256(record_key).hexdigest()[:16]
    return {
        "id": f"live_{record_id}",
        "title": title,
        "company": company or "Not specified",
        "location": metadata.get("location") or ", ".join(
            str(value).strip()
            for value in (metadata.get("city"), metadata.get("state"), metadata.get("country"))
            if value
        ) or "Not specified",
        "experience_years": metadata.get("experience_years"),
        "skills": metadata.get("skills") or [],
        "requirements": metadata.get("requirements") or [],
        "salary_range": metadata.get("salary_range") or "Not disclosed",
        "apply_url": apply_url,
        "source_url": str(source_document.get("url") or apply_url),
        "source": str(metadata.get("platform") or source_name or "Public job API"),
        "platform_source": str(metadata.get("platform") or source_name or "Public job API"),
        "description": str(source_document.get("content") or ""),
        "confidence_score": 86.0,
        "confidence_breakdown": {},
        "human_review_required": False,
        "raw_snippet": str(source_document.get("content") or "")[:500],
    }


def _matches_job_search_preferences(job: Dict[str, Any], query_spec: Dict[str, Any]) -> bool:
    """Keep live results aligned with the role and location shown by the query."""
    if not is_matching_role(
        job.get("title") or job.get("job_title") or "",
        query_spec,
        description=job.get("description", ""),
    ):
        return False

    preferred_locations = query_spec.get("locations") or []
    if preferred_locations:
        location = job.get("location") or job.get("city") or ""
        if not location:
            return False
        location_matches, _ = matches_location_preference(
            str(location),
            preferred_locations,
            bool(query_spec.get("remote")),
        )
        if not location_matches:
            return False

    return True


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
    
    is_job_document = scrape_res.get("success") and is_job_listing_document(scrape_res)
    extracted_records = []
    if req.mode == "job" and req.extract_with_jev and is_job_document:
        extracted_records = jev_extractor.extract_from_firecrawl(scrape_res, query=req.query or "")

    return {
        "status": "success",
        "mode": req.mode,
        "url": req.url,
        "title": scrape_res.get("title"),
        "provider": scrape_res.get("provider"),
        "latency_ms": scrape_res.get("latency_ms", 0),
        "markdown_length": len(scrape_res.get("markdown", "")),
        "raw_snippet": (scrape_res.get("text") or scrape_res.get("markdown") or "")[:450],
        "job_document_accepted": is_job_document,
        "message": (
            "Job listing validated and extracted."
            if req.mode == "job" and is_job_document
            else (
                "The page was scraped as a data source."
                if req.mode == "data"
                else "The page was scraped, but it is not a job listing and was not added to the job feed."
            )
        ),
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

    Job mode accepts only documents that identify as actual vacancies.  Firecrawl
    can still be used for general data scraping with ``mode=data``, but that
    mode is intentionally not allowed to populate the job-results feed.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Search query is required")

    requested_limit = max(1, min(req.limit or 5, 20))
    if req.mode == "data":
        docs = await firecrawl_service.search(req.query.strip(), limit=requested_limit)
        return {
            "status": "success",
            "query": req.query,
            "mode": "data",
            "provider": "firecrawl",
            "raw_documents_found": len(docs),
            "documents": docs[:requested_limit],
            "jobs": [],
        }

    query_spec = parse_job_query_to_spec(req.query.strip()).model_dump()

    # Live public job APIs are the primary source for the job feed.  They work
    # without a Firecrawl key and return posting-shaped records, not articles.
    public_documents = []
    try:
        public_documents = await SourceDiscovery().search(
            req.query.strip(),
            # Apply role/location filters after discovery, so fetch a broader
            # candidate pool before reducing it to the requested result count.
            max_results=min(requested_limit * 4, 20),
        )
    except Exception:
        # Connector-specific failures are logged in SourceDiscovery; proceed to
        # the validated Firecrawl fallback below.
        public_documents = []

    all_jobs = [
        job
        for job in (_to_live_job(document) for document in public_documents)
        if job is not None and _matches_job_search_preferences(job, query_spec)
    ][:requested_limit]

    docs = []
    job_docs = []
    if not all_jobs:
        # Firecrawl remains a secondary job source.  Search extra documents
        # because editorial hits are discarded before Jev extraction.
        search_query = req.query.strip()
        if not any(term in search_query.lower() for term in ("job", "career", "vacanc", "opening", "hiring")):
            search_query = f"{search_query} job openings"
        docs = await firecrawl_service.search(search_query, limit=min(requested_limit * 3, 20))
        job_docs = filter_job_listing_documents(docs)
        for document in job_docs[:requested_limit]:
            extracted_jobs = jev_extractor.extract_from_firecrawl(document, query=req.query)
            all_jobs.extend(
                job for job in extracted_jobs
                if _matches_job_search_preferences(job, query_spec)
            )
        all_jobs = all_jobs[:requested_limit]

    return {
        "status": "success",
        "query": req.query,
        "mode": "job",
        "provider": "public job APIs" if public_documents else "firecrawl",
        "raw_documents_found": len(docs),
        "non_job_documents_filtered": len(docs) - len(job_docs),
        "public_job_documents_found": len(public_documents),
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
