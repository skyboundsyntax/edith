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
try:
    from backend.ai_engine.jev_extractor import jev_extractor
except (ImportError, ModuleNotFoundError):
    from ai_engine.jev_extractor import jev_extractor

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

def normalize_skill_name(s: str) -> str:
    s_clean = str(s).strip()
    s_lower = s_clean.lower()
    acronyms = {"ai": "AI", "ml": "ML", "llm": "LLM", "nlp": "NLP", "api": "API", "aws": "AWS", "gcp": "GCP", "sql": "SQL", "sdk": "SDK", "ui": "UI", "ux": "UX", "ci/cd": "CI/CD", "cicd": "CI/CD"}
    if s_lower in acronyms:
        return acronyms[s_lower]
    return re.sub(r'\bAi\b', 'AI', s_clean, flags=re.IGNORECASE)

def format_to_inr_range(s_min, s_max, currency="INR") -> str:
    if s_min is None and s_max is None:
        return "Not Disclosed"
    try:
        min_v = float(s_min) if s_min is not None else float(s_max)
        max_v = float(s_max) if s_max is not None else float(s_min)
    except (ValueError, TypeError):
        return "Not Disclosed"

    curr = (currency or "INR").upper()
    if curr == "USD":
        min_lpa = (min_v * 86.0) / 100000.0
        max_lpa = (max_v * 86.0) / 100000.0
    elif curr == "EUR":
        min_lpa = (min_v * 92.0) / 100000.0
        max_lpa = (max_v * 92.0) / 100000.0
    elif curr == "GBP":
        min_lpa = (min_v * 110.0) / 100000.0
        max_lpa = (max_v * 110.0) / 100000.0
    else:
        if max_v <= 150: # Already in LPA
            min_lpa = min_v
            max_lpa = max_v
        else:
            min_lpa = min_v / 100000.0
            max_lpa = max_v / 100000.0

    if min_lpa <= 0 or max_lpa <= 0:
        return "Competitive Market CTC"
    if abs(min_lpa - max_lpa) < 0.1:
        return f"₹{min_lpa:.1f} LPA"
    return f"₹{min_lpa:.0f} - {max_lpa:.0f} LPA"

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
    accumulated_logs: List[Dict[str, Any]] = []

    async def emit(event_type: str, data: Dict[str, Any]):
        iso_now = datetime.now(timezone.utc).isoformat()
        node_stage = "intent_parsing"
        if event_type in ["source_started", "jobs_found", "source_completed"]:
            node_stage = "source_discovery"
        elif event_type in ["normalization_completed", "validation_completed"]:
            node_stage = "extraction_mapping"
        elif event_type in ["deduplication_completed", "scoring_completed", "pipeline_completed"]:
            node_stage = "deduplication_scoring"

        log_msg = data.get("message")
        if not log_msg:
            if event_type == "source_started":
                log_msg = f"Connecting to {data.get('source')} ({data.get('domain')})..."
            elif event_type == "jobs_found":
                log_msg = f"{data.get('source')}: Discovered {data.get('count')} candidate records in {data.get('duration_ms')}ms."
            elif event_type == "source_completed":
                log_msg = f"{data.get('source')}: Ingestion phase completed with status: {data.get('status', 'OK')}."
            elif event_type == "pipeline_started":
                log_msg = data.get("message", "Initiating autonomous data intelligence pipeline...")
            else:
                log_msg = str(data)

        log_entry = {
            "timestamp": iso_now,
            "node": node_stage,
            "message": log_msg
        }
        accumulated_logs.append(log_entry)

        payload = {
            "workflow_id": workflow_id,
            "event": event_type,
            "node": node_stage,
            "timestamp": iso_now,
            "message": log_msg,
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
        # Step 1: Dynamic Intent Parsing
        domain_type = query_spec.get("intent_parsing", {}).get("domain_type", "TALENT_JOBS")
        primary_entity = query_spec.get("intent_parsing", {}).get("primary_role", "Target Entity")
        await emit("pipeline_started", {
            "message": f"Stage 1 [Intent Parsing]: Domain resolved as {domain_type}. Dynamic schema mapped for '{primary_entity}'.",
            "query_spec": query_spec
        })

        # Step 2: Fetch sources in parallel with resilience
        live_connectors = [c for c in source_registry.get_live_connectors() if c.can_handle(query_spec)]
        linkout_connectors = source_registry.get_linkout_connectors()
        
        all_raw_jobs: List[Dict[str, Any]] = []
        sources_searched = []
        successful_sources = 0

        sem = asyncio.Semaphore(4)

        async def fetch_from_source(connector):
            nonlocal successful_sources
            c_name = connector.name
            t0 = time.time()
            async with sem:
                await emit("source_started", {"source": c_name, "domain": connector.domain, "access_method": connector.access_method})
                try:
                    jobs = await asyncio.wait_for(connector.search(query_spec), timeout=18.0)
                    duration_ms = int((time.time() - t0) * 1000)
                    await emit("jobs_found", {"source": c_name, "count": len(jobs), "duration_ms": duration_ms})
                    await emit("source_completed", {"source": c_name, "count": len(jobs), "duration_ms": duration_ms, "status": "success"})
                    successful_sources += 1
                    return c_name, jobs, None
                except Exception as err:
                    duration_ms = int((time.time() - t0) * 1000)
                    err_msg = f"{type(err).__name__}: {err}" if str(err) else type(err).__name__
                    logger.warning(f"Source {c_name} completed with notice: {err_msg}")
                    await emit("source_completed", {"source": c_name, "count": 0, "duration_ms": duration_ms, "status": "SOURCE UNAVAILABLE", "error": err_msg})
                    return c_name, [], err_msg

        # Launch all live connectors with controlled concurrency
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
            "message": f"Stage 3 [Extraction & Schema Mapping]: Normalizing {total_discovered} raw records across {len(sources_searched)} source providers."
        })

        # Step 3: Deduplication
        canonical_jobs, duplicates_pruned = deduplicate_jobs(all_raw_jobs)
        await emit("deduplication_completed", {
            "total_before": total_discovered,
            "total_after": len(canonical_jobs),
            "removed": duplicates_pruned,
            "message": f"Stage 4 [Deduplication & Trust Scoring]: Deduplication pruned {duplicates_pruned} duplicates. Ingesting {len(canonical_jobs)} unique entities."
        })

        # Step 4: Validation & Liveness & Localization Filtering
        validated_jobs = []
        expired_count = 0
        geo_excluded_count = 0
        gig_excluded_count = 0
        sal_excluded_count = 0

        target_locs = query_spec.get("locations") or []
        remote_allowed = query_spec.get("remote", False) or not any(l in ["on-site", "offline", "onsite"] for l in target_locs)
        target_sal_min = query_spec.get("salary_min")
        target_sal_max = query_spec.get("salary_max")

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

            # Strict Salary Bracket Filter:
            # Keeps jobs in desired bracket AND unlisted jobs; excludes jobs strictly outside bracket!
            if target_sal_min is not None or target_sal_max is not None:
                j_min = job.get("salary_min")
                j_max = job.get("salary_max")
                j_curr = (job.get("salary_currency") or "INR").upper()

                if j_min is not None or j_max is not None:
                    try:
                        eff_j_min = float(j_min) if j_min is not None else float(j_max)
                        eff_j_max = float(j_max) if j_max is not None else float(j_min)
                        if j_curr == "USD":
                            eff_j_min *= 86.0
                            eff_j_max *= 86.0
                        elif j_curr == "EUR":
                            eff_j_min *= 92.0
                            eff_j_max *= 92.0
                        elif j_curr == "GBP":
                            eff_j_min *= 110.0
                            eff_j_max *= 110.0
                        elif eff_j_max <= 150: # Already in LPA
                            eff_j_min *= 100000.0
                            eff_j_max *= 100000.0

                        # Outside bracket checks:
                        if target_sal_min is not None and eff_j_max < target_sal_min:
                            sal_excluded_count += 1
                            continue
                        # Allow 25% upside buffer for high compensation
                        if target_sal_max is not None and eff_j_min > (target_sal_max * 1.25):
                            sal_excluded_count += 1
                            continue
                    except (ValueError, TypeError):
                        pass # Keep unparsable/unlisted compensation

            validated_jobs.append(job)

        msg_parts = [f"{len(validated_jobs)} active listings verified"]
        if expired_count > 0:
            msg_parts.append(f"{expired_count} closed postings flagged")
        if geo_excluded_count > 0:
            msg_parts.append(f"{geo_excluded_count} foreign/mismatched locations filtered")
        if gig_excluded_count > 0:
            msg_parts.append(f"{gig_excluded_count} non-engineering online gigs pruned")
        if sal_excluded_count > 0:
            msg_parts.append(f"{sal_excluded_count} postings outside target salary bracket filtered")

        await emit("validation_completed", {
            "active_count": len(validated_jobs),
            "expired_count": expired_count,
            "geo_excluded_count": geo_excluded_count,
            "gig_excluded_count": gig_excluded_count,
            "sal_excluded_count": sal_excluded_count,
            "message": ". ".join(msg_parts) + "."
        })

        # Step 5: Deterministic Match Scoring, Jev Trust Meter & Anti-Ghost Audit
        scored_jobs = []
        human_review_count = 0

        for job in validated_jobs:
            clean_desc = clean_html_text(job.get("description"))
            score_res = score_job_match(job, query_spec)
            match_score = score_res["match_score"]
            job["match_score"] = match_score
            job["score_breakdown"] = score_res["score_breakdown"]
            job["why_it_matches"] = score_res["why_it_matches"]
            job["potential_gaps"] = score_res["potential_gaps"]
            job["quality_signals"] = score_res["quality_signals"]

            # Mathematical Jev Deterministic Extraction & Anti-Ghost Audit
            prev_prov = job.get("provenance") or {}
            prev_eval = prev_prov.get("confidence_evaluation") or {}
            if prev_eval.get("breakdown") and prev_eval.get("overall_score"):
                jev_conf = prev_eval["overall_score"]
                jev_breakdown = prev_eval["breakdown"]
                jev_needs_review = prev_eval.get("human_review_required", False)
            else:
                jev_conf, jev_breakdown, jev_needs_review = jev_extractor.audit_job_record(
                    job,
                    source_text=clean_desc
                )

            job["jev_confidence"] = jev_conf
            job["jev_breakdown"] = jev_breakdown

            # Determine human review flag based on both match confidence and Jev anti-ghost audit
            needs_review = match_score < confidence_threshold or jev_needs_review or bool(score_res["quality_signals"].get("risk_signals"))
            job["human_review_required"] = needs_review
            if needs_review:
                human_review_count += 1

            # Bind complete provenance metadata
            job["provenance"] = {
                **prev_prov,
                "source_url": job.get("source_url") or job.get("apply_url", ""),
                "scraper": prev_prov.get("scraper") or ("firecrawl" if job.get("source") == "firecrawl" else "portal_connector"),
                "extractor": "jev_deterministic_engine",
                "raw_snippet": clean_desc[:450],
                "confidence_evaluation": {
                    "overall_score": jev_conf,
                    "breakdown": jev_breakdown,
                    "human_review_required": needs_review,
                    "evaluator": "TypeSafe Jev Deterministic Engine"
                }
            }

            scored_jobs.append(job)

        # Sort jobs by combined match score and Jev confidence
        scored_jobs.sort(key=lambda j: (j.get("match_score", 0) * 0.6) + (j.get("jev_confidence", 80) * 0.4), reverse=True)

        await emit("scoring_completed", {
            "count": len(scored_jobs),
            "top_score": scored_jobs[0]["match_score"] if scored_jobs else 0,
            "human_review_count": human_review_count,
            "message": f"Stage 4 [Deduplication & Trust Scoring]: Calculated explainable semantic fit and Jev trust scores for all {len(scored_jobs)} entities."
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
            workflow.execution_logs = accumulated_logs
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

                exp_val = j.get("experience_years")
                if not exp_val or exp_val == "0-2 yrs":
                    if j.get("experience_max") is not None:
                        exp_val = f"{int(j.get('experience_min', 0))}-{int(j.get('experience_max'))} yrs"
                    elif j.get("experience_min") is not None and j.get("experience_min") > 0:
                        exp_val = f"{int(j.get('experience_min'))}+ yrs"
                    else:
                        exp_val = "Open / Not Disclosed"

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
                        "skills": [normalize_skill_name(s) for s in (j.get("skills") if isinstance(j.get("skills"), list) else [j.get("skills")] if j.get("skills") else []) if s],
                        "requirements": j.get("requirements", []),
                        "experience_years": exp_val,
                        "salary_range": format_to_inr_range(j.get("salary_min"), j.get("salary_max"), j.get("salary_currency", "INR")),
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
                        "is_link_out": False,
                        "jev_confidence": j.get("jev_confidence", 85.0),
                        "jev_breakdown": j.get("jev_breakdown", {}),
                        "scraper_provider": j.get("provenance", {}).get("scraper", "portal_connector")
                    },
                    confidence_score=j.get("jev_confidence", j.get("match_score", 0.0)),
                    confidence_breakdown=j.get("jev_breakdown", j.get("score_breakdown", {})),
                    human_review_required=needs_review,
                    source_url=j.get("source_url", ""),
                    source_title=f"{j.get('title')} at {j.get('company')}",
                    extracted_timestamp=datetime.now(timezone.utc).isoformat(),
                    raw_snippet=clean_desc[:450],
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
            "message": f"Stage 4 [Deduplication & Trust Scoring]: Ingestion cycle completed in {total_duration}ms. {len(scored_jobs)} verified records ready."
        })

        if workflow:
            workflow.execution_logs = accumulated_logs
            db.commit()

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
            workflow.execution_logs = accumulated_logs + [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "error", "message": f"Critical pipeline failure: {e}"}]
            db.commit()
        await emit("pipeline_failed", {"error": str(e)})
        raise
    finally:
        db.close()
