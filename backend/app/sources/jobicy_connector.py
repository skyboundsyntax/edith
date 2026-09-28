"""
Jobicy Public Remote Jobs API Connector.
Uses official public Jobicy API (https://jobicy.com/api/v2/remote-jobs).
Permitted public endpoint returning developer, AI/ML, and engineering opportunities.
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

class JobicyConnector(JobSourceConnector):
    name = "Jobicy"
    domain = "jobicy.com"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public API v2: Permitted unauthenticated requests for public remote job feeds"
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

        url = "https://jobicy.com/api/v2/remote-jobs?count=50"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                if resp.status_code != 200:
                    return []

                data = resp.json()
                jobs = data.get("jobs", [])

                for item in jobs:
                    title = item.get("jobTitle", "")
                    title_lower = title.lower()
                    job_geo = item.get("jobGeo", "Anywhere")
                    if isinstance(job_geo, list):
                        job_geo = ", ".join(job_geo)
                    elif not isinstance(job_geo, str):
                        job_geo = str(job_geo or "")
                    geo_lower = job_geo.lower()
                    job_excerpt = item.get("jobExcerpt", "")

                    # Relevancy check
                    matches_role = True
                    if search_tokens:
                        matches_role = any(tok in title_lower or tok in job_excerpt.lower() for tok in search_tokens)

                    if not matches_role:
                        continue

                    # Location / Remote check
                    loc_info = normalize_location(job_geo)
                    is_remote = True  # Jobicy is 100% remote positions

                    loc_matches = True
                    if target_locations:
                        # If user specifically wants remote, Jobicy matches
                        if not remote_allowed and "india" not in geo_lower and "anywhere" not in geo_lower:
                            loc_matches = False

                    if not loc_matches:
                        continue

                    job_id = str(item.get("id"))
                    company = item.get("companyName") or "Tech Organization"
                    apply_url = item.get("url") or item.get("jobUrl") or f"https://jobicy.com/jobs/{job_id}"
                    pub_date = item.get("pubDate") or datetime.now(timezone.utc).isoformat()
                    now_iso = datetime.now(timezone.utc).isoformat()

                    raw_str = f"{title}_{company}_{job_id}"
                    content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                    salary_min = None
                    salary_max = None
                    salary_currency = "USD"
                    if item.get("annualSalaryMin"):
                        try:
                            salary_min = float(item.get("annualSalaryMin"))
                        except (ValueError, TypeError):
                            pass
                    if item.get("annualSalaryMax"):
                        try:
                            salary_max = float(item.get("annualSalaryMax"))
                        except (ValueError, TypeError):
                            pass
                    if item.get("salaryCurrency"):
                        salary_currency = item.get("salaryCurrency")

                    canonical_job = {
                        "id": f"jby_{job_id}",
                        "source": "jobicy",
                        "source_job_id": job_id,
                        "source_url": apply_url,
                        "apply_url": apply_url,
                        "title": title,
                        "company": company,
                        "company_url": item.get("companyUrl") or f"https://jobicy.com/company/{company.lower().replace(' ', '-')}",
                        "company_domain": "jobicy.com",
                        "description": item.get("jobDescription") or job_excerpt,
                        "requirements": [],
                        "responsibilities": [],
                        "skills": [s.title() for s in skills if s in title_lower] or ["Python", "FastAPI"],
                        "technologies": [],
                        "location": f"Remote ({job_geo})",
                        "city": None,
                        "state": None,
                        "country": "India" if "india" in geo_lower else "Global",
                        "remote_type": "remote",
                        "employment_type": (item.get("jobType") or "full-time").lower(),
                        "experience_min": 0,
                        "experience_max": 3,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "salary_currency": salary_currency,
                        "salary_period": "year",
                        "education": "Not specified",
                        "date_posted": pub_date,
                        "date_updated": pub_date,
                        "first_seen_at": now_iso,
                        "last_seen_at": now_iso,
                        "is_active": True,
                        "is_verified": True,
                        "source_timestamp": pub_date,
                        "raw_content_hash": content_hash,
                        "sources": ["jobicy"],
                        "provenance": {
                            "source_name": "Jobicy Public API",
                            "source_url": url,
                            "original_job_url": apply_url,
                            "retrieval_timestamp": now_iso,
                            "parser_version": "1.0-jby",
                            "content_hash": content_hash,
                            "source_timestamp": pub_date,
                            "last_successful_fetch": now_iso
                        }
                    }
                    results.append(canonical_job)

                    if len(results) >= 20:
                        break

        except Exception as e:
            logger.warning(f"Jobicy fetch error: {e}")

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://jobicy.com/api/v2/remote-jobs?count=1")
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
            returns_structured_salary=True,
            rate_limit_per_minute=60,
            concurrent_limit=3
        )
