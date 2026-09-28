"""
Ashby Public Job Postings API Connector.
Uses official public Ashby postings endpoint (https://api.ashbyhq.com/posting-api/job-board/{organization}).
Permitted, unauthenticated GET requests according to Ashby public board standards.
"""
import time
import httpx
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from backend.app.sources.base import JobSourceConnector, SourceHealth, SourceCapabilities
from backend.app.locations.india_locations import normalize_location

logger = logging.getLogger(__name__)

ASHBY_COMPANIES = [
    {"token": "linear", "company": "Linear", "domain": "linear.app"},
    {"token": "perplexity", "company": "Perplexity", "domain": "perplexity.ai"},
    {"token": "cursor", "company": "Cursor", "domain": "cursor.com"},
    {"token": "supabase", "company": "Supabase", "domain": "supabase.com"},
    {"token": "vercel", "company": "Vercel", "domain": "vercel.com"}
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
        keywords = [k.lower() for k in (query_spec.get("keywords") or [])]
        roles = [r.lower() for r in (query_spec.get("roles") or [])]
        skills = [s.lower() for s in (query_spec.get("skills") or [])]
        target_locations = [l.lower() for l in (query_spec.get("locations") or [])]
        remote_allowed = query_spec.get("remote", True)

        search_tokens = set(keywords + roles + skills)

        async with httpx.AsyncClient(timeout=8.0) as client:
            for comp in ASHBY_COMPANIES:
                org_token = comp["token"]
                company_name = comp["company"]
                company_domain = comp["domain"]
                url = f"https://api.ashbyhq.com/posting-api/job-board/{org_token}"

                try:
                    resp = await client.get(url, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    job_postings = data.get("jobs", [])

                    for item in job_postings:
                        title = item.get("title", "")
                        title_lower = title.lower()

                        loc_raw = item.get("location") or ""
                        loc_lower = loc_raw.lower()
                        is_remote_flag = item.get("isRemote", False)
                        dept = item.get("department") or ""

                        # Relevancy check
                        matches_role = True
                        if search_tokens:
                            matches_role = any(tok in title_lower for tok in search_tokens)
                            if not matches_role and dept:
                                matches_role = any(tok in dept.lower() for tok in search_tokens)

                        if not matches_role:
                            continue

                        # Location check
                        loc_info = normalize_location(loc_raw)
                        is_remote = is_remote_flag or loc_info["remote_type"] == "remote" or "remote" in loc_lower

                        loc_matches = True
                        if target_locations:
                            loc_matches = False
                            if remote_allowed and is_remote:
                                loc_matches = True
                            elif any(target in loc_lower or target in (loc_info.get("city") or "").lower() for target in target_locations):
                                loc_matches = True
                            elif "india" in loc_lower or loc_info.get("country") == "India":
                                loc_matches = True

                        if not loc_matches:
                            continue

                        job_id = str(item.get("id"))
                        apply_url = item.get("jobUrl") or f"https://jobs.ashbyhq.com/{org_token}/{job_id}"
                        now_iso = datetime.now(timezone.utc).isoformat()
                        published_at = item.get("publishedAt") or now_iso

                        raw_str = f"{title}_{company_name}_{job_id}_{loc_raw}"
                        content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

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
                            "description": f"Role: {title} at {company_name}. Department: {dept}. Location: {loc_raw}.",
                            "requirements": [],
                            "responsibilities": [],
                            "skills": [s.title() for s in skills if s in title_lower] or ["Software Development"],
                            "technologies": [],
                            "location": loc_info["canonical_location"],
                            "city": loc_info["city"],
                            "state": loc_info["state"],
                            "country": loc_info["country"],
                            "remote_type": "remote" if is_remote else loc_info["remote_type"],
                            "employment_type": (item.get("employmentType") or "full-time").lower(),
                            "experience_min": 0,
                            "experience_max": 2 if "intern" in title_lower or "junior" in title_lower else 5,
                            "salary_min": None,
                            "salary_max": None,
                            "salary_currency": "INR",
                            "salary_period": "year",
                            "education": "Relevant software engineering experience or degree",
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
                                "parser_version": "1.0-ash",
                                "content_hash": content_hash,
                                "source_timestamp": published_at,
                                "last_successful_fetch": now_iso
                            }
                        }
                        results.append(canonical_job)

                        if len(results) >= 20:
                            break
                except Exception as e:
                    logger.warning(f"Ashby fetch error for {org_token}: {e}")
                    continue

                if len(results) >= 20:
                    break

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
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
                status="UNAVAILABLE",
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
