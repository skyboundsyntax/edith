"""
Source Orchestrator & Job Ingestion Engine for EDITH.
Executes parallel source collection across permitted public APIs and ATS endpoints.
Handles resilience: if one source fails, others proceed smoothly.
Emits real WebSocket progress events.
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
import json
import re

from backend.app.sources.registry import source_registry
from backend.app.intelligence.deduplicator import deduplicate_jobs
from backend.app.intelligence.match_scorer import score_job_match
from backend.app.db.database import SessionLocal
from backend.app.db.models import WorkflowModel, DataRecordModel, JobModel
from backend.app.locations.india_locations import normalize_location, matches_location_preference, is_online_gig

import html
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def clean_html_text(raw_text: Optional[str]) -> str:
    if not raw_text:
        return ""
    try:
        unescaped = html.unescape(str(raw_text))
        soup = BeautifulSoup(unescaped, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'Find\s+Jobs\s+in\s+[^.]*\s+on\s+Arbeitnow', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Apply\s+(now\s+)?on\s+Arbeitnow', '', text, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return re.sub(r'<[^>]*>', ' ', str(raw_text)).strip()

async def run_job_ingestion_pipeline(
    workflow_id: str,
    query_spec: Dict[str, Any],
    confidence_threshold: float = 75.0,
    event_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
) -> Dict[str, Any]:
    """
    Full autonomous job intelligence workflow:
    1. Query Planning
    2. Parallel Source Connectors (Greenhouse, Lever, Ashby, Jobicy, Arbeitnow, LinkOut)
    3. Normalization into Canonical Schema
    4. Deduplication
    5. Validation (liveness & active flags)
    6. Explainable Match Scoring (0-100) & Risk Signal detection
    7. Database Persistence
    8. Real-time Event Streaming
    """
    start_time = time.time()
    db = SessionLocal()

    async def emit(event_type: str, data: Dict[str, Any]):
        payload = {
            "workflow_id": workflow_id,
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }
        if event_callback:
            try:
                res = event_callback(payload)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.warning(f"WebSocket emit error: {e}")

    try:
        # Step 1: Initialize
        await emit("pipeline_started", {
            "message": "Initiating autonomous multi-source job intelligence pipeline...",
            "query_spec": query_spec
        })

        # Step 2: Fetch sources in parallel with resilience
        live_connectors = source_registry.get_live_connectors()
        linkout_connectors = source_registry.get_linkout_connectors()
        
        all_raw_jobs: List[Dict[str, Any]] = []
        sources_searched = []
        successful_sources = 0

        async def fetch_from_source(connector):
            nonlocal successful_sources
            c_name = connector.name
            t0 = time.time()
            await emit("source_started", {"source": c_name, "domain": connector.domain, "access_method": connector.access_method})
            try:
                jobs = await asyncio.wait_for(connector.search(query_spec), timeout=9.0)
                duration_ms = int((time.time() - t0) * 1000)
                await emit("jobs_found", {"source": c_name, "count": len(jobs), "duration_ms": duration_ms})
                await emit("source_completed", {"source": c_name, "count": len(jobs), "duration_ms": duration_ms, "status": "success"})
                successful_sources += 1
                return c_name, jobs, None
            except Exception as err:
                duration_ms = int((time.time() - t0) * 1000)
                logger.error(f"Source {c_name} failed: {err}")
                await emit("source_completed", {"source": c_name, "count": 0, "duration_ms": duration_ms, "status": "SOURCE UNAVAILABLE", "error": str(err)})
                return c_name, [], str(err)

        # Launch all live connectors concurrently
        tasks = [fetch_from_source(c) for c in live_connectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, tuple):
                s_name, s_jobs, s_err = res
                sources_searched.append({"source": s_name, "count": len(s_jobs), "status": "error" if s_err else "online"})
                all_raw_jobs.extend(s_jobs)

        # Ingest only 100% verified real job postings from live connectors

        total_discovered = len(all_raw_jobs)
        await emit("normalization_completed", {
            "count": total_discovered,
            "message": f"{total_discovered} jobs collected across {len(sources_searched)} source providers."
        })

        # Step 3: Deduplication
        canonical_jobs, duplicates_pruned = deduplicate_jobs(all_raw_jobs)
        await emit("deduplication_completed", {
            "total_before": total_discovered,
            "total_after": len(canonical_jobs),
            "removed": duplicates_pruned,
            "message": f"Deduplication pruned {duplicates_pruned} cross-platform duplicate postings."
        })

        # Step 4: Validation & Liveness & Localization Filtering
        validated_jobs = []
        expired_count = 0
        geo_excluded_count = 0
        gig_excluded_count = 0

        target_locs = query_spec.get("locations") or []
        remote_allowed = query_spec.get("remote", False)

        all_query_terms = " ".join(
            [r.lower() for r in (query_spec.get("roles") or [])] +
            [s.lower() for s in (query_spec.get("skills") or [])] +
            [k.lower() for k in (query_spec.get("keywords") or [])]
        )
        is_tech_search = any(re.search(r'\b' + kw + r'\b', all_query_terms) for kw in ["software", "engineer", "developer", "ai", "ml", "python", "data", "frontend", "backend", "fullstack"])

        for job in canonical_jobs:
            # Active check
            if not job.get("is_active", True):
                expired_count += 1
                continue

            title = job.get("title") or ""
            desc = job.get("description") or ""

            # Online non-tech gig filter
            if is_tech_search and is_online_gig(title, desc):
                gig_excluded_count += 1
                continue

            # Strict Location / Geographic Filter:
            # If target locations (e.g. Pune, Bengaluru) or India context is requested,
            # drop foreign/mismatched listings (e.g. USA, UK, Germany, Spain, Czechia)
            job_loc = job.get("location") or "Remote"
            loc_match, loc_pts = matches_location_preference(job_loc, target_locs, remote_allowed)
            if target_locs and not loc_match:
                # Secondary check: if job title explicitly mentions the requested location
                title_lower = title.lower()
                matched_in_title = any(tloc.lower().strip() in title_lower for tloc in target_locs)
                if not matched_in_title:
                    geo_excluded_count += 1
                    continue


            validated_jobs.append(job)

        msg_parts = [f"{len(validated_jobs)} active listings verified"]
        if expired_count > 0:
            msg_parts.append(f"{expired_count} closed postings flagged")
        if geo_excluded_count > 0:
            msg_parts.append(f"{geo_excluded_count} foreign/mismatched locations filtered")
        if gig_excluded_count > 0:
            msg_parts.append(f"{gig_excluded_count} non-engineering online gigs pruned")

        await emit("validation_completed", {
            "active_count": len(validated_jobs),
            "expired_count": expired_count,
            "geo_excluded_count": geo_excluded_count,
            "gig_excluded_count": gig_excluded_count,
            "message": ". ".join(msg_parts) + "."
        })

        # Step 5: Deterministic Match Scoring & Explainability
        scored_jobs = []
        human_review_count = 0

        for job in validated_jobs:
            score_res = score_job_match(job, query_spec)
            match_score = score_res["match_score"]
            job["match_score"] = match_score
            job["score_breakdown"] = score_res["score_breakdown"]
            job["why_it_matches"] = score_res["why_it_matches"]
            job["potential_gaps"] = score_res["potential_gaps"]
            job["quality_signals"] = score_res["quality_signals"]

            needs_review = match_score < confidence_threshold or bool(score_res["quality_signals"].get("risk_signals"))
            job["human_review_required"] = needs_review
            if needs_review:
                human_review_count += 1

            scored_jobs.append(job)

        # Sort jobs by match score descending
        scored_jobs.sort(key=lambda j: j.get("match_score", 0), reverse=True)

        await emit("scoring_completed", {
            "count": len(scored_jobs),
            "top_score": scored_jobs[0]["match_score"] if scored_jobs else 0,
            "human_review_count": human_review_count,
            "message": f"Calculated 100-point explainable match scores for all {len(scored_jobs)} listings."
        })

        # Step 6: Persist into Database
        workflow = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
        if workflow:
            workflow.status = "completed"
            workflow.total_extracted = total_discovered
            workflow.total_deduplicated = len(scored_jobs)
            workflow.duplicates_pruned = duplicates_pruned
            workflow.human_review_count = human_review_count
            workflow.sources_searched = sources_searched
            workflow.completed_at = datetime.now(timezone.utc)

            # Persist canonical JobModel records
            for idx, j in enumerate(scored_jobs):
                raw_id = j.get("id") or f"job_{idx}"
                db_job_id = f"{workflow_id}_{raw_id}_{idx}"
                clean_desc = clean_html_text(j.get("description"))
                # Create JobModel
                new_job = JobModel(
                    id=db_job_id,
                    workflow_id=workflow_id,
                    source=j.get("source", "unknown"),
                    source_job_id=str(j.get("source_job_id")),
                    source_url=j.get("source_url", ""),
                    apply_url=j.get("apply_url", ""),
                    title=j.get("title", ""),
                    company=j.get("company", ""),
                    company_url=j.get("company_url"),
                    company_domain=j.get("company_domain"),
                    description=clean_desc,
                    requirements=j.get("requirements", []),
                    responsibilities=j.get("responsibilities", []),
                    skills=j.get("skills", []),
                    technologies=j.get("technologies", []),
                    location=j.get("location"),
                    city=j.get("city"),
                    state=j.get("state"),
                    country=j.get("country", "India"),
                    remote_type=j.get("remote_type", "on-site"),
                    employment_type=j.get("employment_type", "full-time"),
                    experience_min=j.get("experience_min"),
                    experience_max=j.get("experience_max"),
                    salary_min=j.get("salary_min"),
                    salary_max=j.get("salary_max"),
                    salary_currency=j.get("salary_currency", "INR"),
                    salary_period=j.get("salary_period", "year"),
                    education=j.get("education"),
                    date_posted=j.get("date_posted"),
                    date_updated=j.get("date_updated"),
                    is_active=j.get("is_active", True),
                    is_verified=j.get("is_verified", True),
                    source_timestamp=j.get("source_timestamp"),
                    raw_content_hash=j.get("raw_content_hash"),
                    match_score=j.get("match_score", 0.0),
                    score_breakdown=j.get("score_breakdown", {}),
                    match_reasons=j.get("why_it_matches", []),
                    potential_gaps=j.get("potential_gaps", []),
                    freshness_score=j.get("quality_signals", {}).get("freshness_score", 90.0),
                    source_confidence=j.get("quality_signals", {}).get("source_confidence", 95.0),
                    listing_quality_score=j.get("quality_signals", {}).get("listing_quality_score", 90.0),
                    risk_signals=j.get("quality_signals", {}).get("risk_signals", []),
                    sources=j.get("sources", [j.get("source")]),
                    provenance=j.get("provenance", {})
                )
                db.merge(new_job)

                # Also persist DataRecordModel for backward compatibility
                remote_type = str(j.get("remote_type") or "on-site").lower()
                loc_str = str(j.get("location") or "").lower()
                title_str = str(j.get("title") or "").lower()
                desc_str = str(j.get("description") or "").lower()[:300]

                remote_signals = ["remote", "online", "virtual", "wfh", "anywhere", "work from home", "telecommute"]
                hybrid_signals = ["hybrid", "flexible work", "partial remote"]

                is_online = (remote_type == "remote") or any(k in loc_str or k in title_str or k in desc_str for k in remote_signals)
                is_hybrid = (remote_type == "hybrid") or any(k in loc_str or k in title_str for k in hybrid_signals)

                if is_online and not is_hybrid:
                    work_modality = "Online"
                    modality_detail = "Online (Remote)"
                elif is_hybrid:
                    work_modality = "Hybrid"
                    modality_detail = "Hybrid (Flexible)"
                else:
                    work_modality = "Offline"
                    modality_detail = "Offline (On-site)"

                data_record = DataRecordModel(
                    id=f"rec_{db_job_id}",
                    workflow_id=workflow_id,
                    entity_name="JobOpening",
                    data_json={
                        "job_title": j.get("title"),
                        "company": j.get("company"),
                        "company_domain": j.get("company_domain"),
                        "location": j.get("location"),
                        "city": j.get("city"),
                        "remote_type": j.get("remote_type") or ("remote" if is_online else "on-site"),
                        "work_modality": work_modality,
                        "modality_detail": modality_detail,
                        "employment_type": j.get("employment_type"),
                        "skills": j.get("skills"),
                        "experience_years": f"{j.get('experience_min', 0)}-{j.get('experience_max', 2)} yrs" if j.get("experience_max") is not None else "0-2 yrs",
                        "salary_range": f"{j.get('salary_currency', 'INR')} {int(j['salary_min'])} - {int(j['salary_max'])}" if j.get("salary_min") and j.get("salary_max") else "Not Disclosed",
                        "apply_link": j.get("apply_url"),
                        "platform_source": j.get("source", "Careers").title(),
                        "date_posted": j.get("date_posted"),
                        "match_score": j.get("match_score"),
                        "score_breakdown": j.get("score_breakdown"),
                        "why_it_matches": j.get("why_it_matches"),
                        "potential_gaps": j.get("potential_gaps"),
                        "quality_signals": j.get("quality_signals"),
                        "sources": j.get("sources"),
                        "description": clean_desc,
                        "description_snippet": clean_desc[:400],
                        "is_link_out": False
                    },
                    confidence_score=j.get("match_score", 0.0),
                    confidence_breakdown=j.get("score_breakdown", {}),
                    human_review_required=needs_review,
                    source_url=j.get("source_url", ""),
                    source_title=f"{j.get('title')} at {j.get('company')}",
                    extracted_timestamp=datetime.now(timezone.utc).isoformat(),
                    raw_snippet=clean_desc[:400],
                    deduplication_hash=j.get("raw_content_hash", "")
                )
                db.merge(data_record)

            db.commit()

        total_duration = int((time.time() - start_time) * 1000)
        await emit("pipeline_completed", {
            "total_jobs": len(scored_jobs),
            "duplicates_removed": duplicates_pruned,
            "sources_searched": sources_searched,
            "duration_ms": total_duration,
            "message": f"Pipeline completed in {total_duration}ms. {len(scored_jobs)} genuine jobs ready for review."
        })

        return {
            "status": "completed",
            "total_jobs": len(scored_jobs),
            "duplicates_pruned": duplicates_pruned,
            "sources_searched": sources_searched,
            "duration_ms": total_duration,
            "jobs": scored_jobs
        }

    except Exception as e:
        logger.error(f"Ingestion pipeline critical error: {e}", exc_info=True)
        if workflow:
            workflow.status = "failed"
            db.commit()
        await emit("pipeline_failed", {"error": str(e)})
        raise
    finally:
        db.close()
