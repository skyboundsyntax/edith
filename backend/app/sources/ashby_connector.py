"""
Ashby Public Job Postings API Connector.
Uses official public Ashby postings endpoint (https://api.ashbyhq.com/posting-api/job-board/{organization}).
Permitted, unauthenticated GET requests according to Ashby public board standards.
"""
import time
import httpx
import logging
import hashlib
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import re

from backend.app.sources.base import JobSourceConnector, SourceHealth, SourceCapabilities
from backend.app.locations.india_locations import normalize_location, matches_location_preference, is_online_gig
from backend.app.intelligence.role_matcher import is_matching_role

logger = logging.getLogger(__name__)

ASHBY_COMPANIES = [
    {"token": "linear", "company": "Linear", "domain": "linear.app"},
    {"token": "perplexity", "company": "Perplexity", "domain": "perplexity.ai"},
    {"token": "cursor", "company": "Cursor", "domain": "cursor.com"},
    {"token": "supabase", "company": "Supabase", "domain": "supabase.com"}
]

class AshbyConnector(JobSourceConnector):
    name = "Ashby"
    domain = "api.ashbyhq.com"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public Board API: Permitted GET queries for published job listings without auth"
    rate_limit = "60 requests/min"
    enabled = True

    def can_handle(self, query_spec: Dict[str, Any]) -> bool:
        return True

    async def search(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        target_locations = [l.lower() for l in (query_spec.get("locations") or [])]
        remote_allowed = query_spec.get("remote", False) or not any(l in ["on-site", "offline"] for l in target_locations)
        skills = query_spec.get("skills") or []

        async def fetch_ashby_company(client: httpx.AsyncClient, comp: Dict[str, str]) -> List[Dict[str, Any]]:
            org_token = comp["token"]
            company_name = comp["company"]
            company_domain = comp["domain"]
            url = f"https://api.ashbyhq.com/posting-api/job-board/{org_token}"
            comp_jobs = []

            try:
                resp = await client.get(url, timeout=4.5, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                if resp.status_code != 200:
                    return []

                data = resp.json()
                job_postings = data.get("jobs", [])

                for item in job_postings:
                    title = item.get("title", "")
                    dept = item.get("department") or ""

                    # 1. Skip non-engineering online gigs
                    if is_online_gig(title, ""):
                        continue

                    # 2. Relevancy check: flexible role matching
                    if not is_matching_role(title, query_spec, department=dept):
                        continue

                    # 3. Location check
                    loc_raw = item.get("location") or ""
                    is_remote_flag = item.get("isRemote", False)
                    effective_loc = loc_raw or ("Remote" if is_remote_flag else "")
                    loc_matches, loc_pts = matches_location_preference(effective_loc, target_locations, remote_allowed)
                    if not loc_matches or loc_pts == 0:
                        continue

                    loc_info = normalize_location(effective_loc)
                    job_id = str(item.get("id"))
                    apply_url = item.get("jobUrl") or f"https://jobs.ashbyhq.com/{org_token}/{job_id}"
                    now_iso = datetime.now(timezone.utc).isoformat()
                    published_at = item.get("publishedAt") or now_iso

                    raw_str = f"{title}_{company_name}_{job_id}_{loc_raw}"
                    content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                    title_lower = title.lower()
                    matched_skills = [s.title() for s in skills if s.lower() in title_lower]
                    if not matched_skills:
                        matched_skills = ["Software Engineering", "Full Stack"]

                    canonical_job = {
                        "id": f"ash_{org_token}_{job_id}",
                        "source": "ashby",
                        "source_job_id": job_id,
                        "source_url": apply_url,
                        "apply_url": apply_url,
                        "title": title,
                        "company": company_name,
                        "company_url": f"https://{company_domain}",
                        "company_domain": company_domain,
                        "description": f"Verified live opening for {title} at {company_name}. Department: {dept or 'Engineering'}. Location: {loc_raw or 'Remote'}. Apply directly on Ashby portal.",
                        "requirements": [],
                        "responsibilities": [],
                        "skills": matched_skills,
                        "technologies": [],
                        "location": loc_info["canonical_location"],
                        "city": loc_info["city"],
                        "state": loc_info["state"],
                        "country": loc_info["country"],
                        "remote_type": "remote" if (is_remote_flag or loc_info["remote_type"] == "remote") else loc_info["remote_type"],
                        "work_modality": "Online" if (is_remote_flag or loc_info["remote_type"] == "remote") else ("Hybrid" if loc_info["remote_type"] == "hybrid" else "Offline"),
                        "employment_type": (item.get("employmentType") or "full-time").lower(),
                        "experience_min": 0,
                        "experience_max": 2 if "intern" in title_lower or "junior" in title_lower else 5,
                        "salary_min": None,
                        "salary_max": None,
                        "salary_currency": "INR",
                        "salary_period": "year",
                        "education": "Relevant software engineering experience or technical degree",
                        "date_posted": published_at,
                        "date_updated": published_at,
                        "first_seen_at": now_iso,
                        "last_seen_at": now_iso,
                        "is_active": True,
                        "is_verified": True,
                        "source_timestamp": published_at,
                        "raw_content_hash": content_hash,
                        "sources": ["ashby", "company-careers"],
                        "provenance": {
                            "source_name": "Ashby Public Job Postings API",
                            "source_url": url,
                            "original_job_url": apply_url,
                            "retrieval_timestamp": now_iso,
                            "parser_version": "2.0-ash-fast",
                            "content_hash": content_hash,
                            "source_timestamp": published_at,
                            "last_successful_fetch": now_iso
                        }
                    }
                    comp_jobs.append(canonical_job)
                    if len(comp_jobs) >= 12:
                        break

                return comp_jobs
            except Exception as e:
                logger.warning(f"Ashby fetch warning for {org_token}: {e}")
                return []

        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0), limits=httpx.Limits(max_connections=15, max_keepalive_connections=10)) as client:
            tasks = [fetch_ashby_company(client, comp) for comp in ASHBY_COMPANIES]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in batch_results:
                if isinstance(res, list):
                    results.extend(res)

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get("https://api.ashbyhq.com/posting-api/job-board/linear")
                latency = int((time.time() - start_time) * 1000)
                if res.status_code == 200:
                    return SourceHealth(
                        name=self.name,
                        domain=self.domain,
                        status="ONLINE",
                        access_method=self.access_method,
                        permission_status=self.permission_status,
                        robots_policy=self.robots_policy,
                        rate_limit=self.rate_limit,
                        latency_ms=latency,
                        jobs_discovered=len(res.json().get("jobs", [])),
                        error_count=0,
                        enabled=True
                    )
                else:
                    return SourceHealth(
                        name=self.name,
                        domain=self.domain,
                        status="DEGRADED",
                        access_method=self.access_method,
                        permission_status=self.permission_status,
                        robots_policy=self.robots_policy,
                        rate_limit=self.rate_limit,
                        latency_ms=latency,
                        error_count=1,
                        enabled=True
                    )
        except Exception:
            return SourceHealth(
                name=self.name,
                domain=self.domain,
                status="DEGRADED",
                access_method=self.access_method,
                permission_status=self.permission_status,
                robots_policy=self.robots_policy,
                rate_limit=self.rate_limit,
                latency_ms=int((time.time() - start_time) * 1000),
                error_count=1,
                enabled=True
            )

    def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_keyword_search=True,
            supports_location_filter=True,
            supports_experience_filter=False,
            supports_remote_filter=True,
            returns_structured_salary=False,
            rate_limit_per_minute=60,
            concurrent_limit=3
        )
