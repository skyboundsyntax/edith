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
import re
import html
from bs4 import BeautifulSoup

from backend.app.sources.base import JobSourceConnector, SourceHealth, SourceCapabilities
from backend.app.locations.india_locations import normalize_location, matches_location_preference, is_online_gig
from backend.app.intelligence.role_matcher import is_matching_role

logger = logging.getLogger(__name__)

def clean_html_snippet(raw_text: str) -> str:
    if not raw_text:
        return ""
    unescaped = html.unescape(raw_text)
    soup = BeautifulSoup(unescaped, "html.parser")
    clean = soup.get_text(separator=" ", strip=True)
    return re.sub(r'\s+', ' ', clean).strip()

class JobicyConnector(JobSourceConnector):
    name = "Jobicy"
    domain = "jobicy.com"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public API v2: Permitted unauthenticated requests for public remote job feeds"
    rate_limit = "60 requests/min"
    enabled = True

    def can_handle(self, query_spec: Dict[str, Any]) -> bool:
        keywords = [k.lower() for k in (query_spec.get("keywords") or [])]
        if any("on-site only" in k or "onsite only" in k or "offline only" in k for k in keywords):
            return False
        return True

    async def search(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        target_locations = [l.lower() for l in (query_spec.get("locations") or [])]
        remote_allowed = query_spec.get("remote", False) or not any(l in ["on-site", "offline"] for l in target_locations)
        skills = query_spec.get("skills") or []

        url = "https://jobicy.com/api/v2/remote-jobs?count=50"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0)) as client:
                resp = await client.get(url, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                if resp.status_code != 200:
                    return []

                data = resp.json()
                jobs = data.get("jobs", [])

                for item in jobs:
                    title = item.get("jobTitle", "")
                    job_excerpt = item.get("jobExcerpt", "")
                    job_geo = item.get("jobGeo", "Anywhere")
                    if isinstance(job_geo, list):
                        job_geo = ", ".join(job_geo)
                    elif not isinstance(job_geo, str):
                        job_geo = str(job_geo or "Anywhere")

                    # 1. Skip scam online gigs (respect user intent)
                    if is_online_gig(title, job_excerpt, query_spec):
                        continue

                    # 2. Check role relevance with flexible matcher
                    if not is_matching_role(title, query_spec, description=job_excerpt):
                        continue

                    # 3. Location check: Jobicy jobs are remote by definition
                    effective_loc = f"{job_geo} (Remote)" if "remote" not in job_geo.lower() else job_geo
                    loc_matches, loc_pts = matches_location_preference(effective_loc, target_locations, remote_allowed)
                    if not loc_matches or loc_pts == 0:
                        continue

                    loc_info = normalize_location(effective_loc)
                    job_id = str(item.get("id"))
                    company = item.get("companyName") or "Tech Organization"
                    apply_url = item.get("url") or item.get("jobUrl") or f"https://jobicy.com/jobs/{job_id}"
                    pub_date = item.get("pubDate") or datetime.now(timezone.utc).isoformat()
                    now_iso = datetime.now(timezone.utc).isoformat()

                    raw_str = f"{title}_{company}_{job_id}"
                    content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                    salary_min = None
                    salary_max = None
                    salary_currency = item.get("salaryCurrency") or "USD"
                    s_min_raw = item.get("salaryMin") or item.get("annualSalaryMin")
                    s_max_raw = item.get("salaryMax") or item.get("annualSalaryMax")
                    if s_min_raw is not None:
                        try:
                            salary_min = float(s_min_raw)
                        except (ValueError, TypeError):
                            pass
                    if s_max_raw is not None:
                        try:
                            salary_max = float(s_max_raw)
                        except (ValueError, TypeError):
                            pass

                    job_type_raw = item.get("jobType")
                    if isinstance(job_type_raw, list):
                        employment_type = str(job_type_raw[0]).lower() if job_type_raw else "full-time"
                    else:
                        employment_type = str(job_type_raw or "full-time").lower()

                    title_lower = title.lower()
                    matched_skills = [s.title() for s in skills if s.lower() in title_lower or s.lower() in job_excerpt.lower()]
                    if not matched_skills:
                        matched_skills = [s.title() for s in skills[:3]] if skills else [title.split()[0].title(), "Communication"]

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
                        "description": clean_html_snippet(item.get("jobDescription") or job_excerpt),
                        "requirements": [],
                        "responsibilities": [],
                        "skills": matched_skills,
                        "technologies": [],
                        "location": loc_info["canonical_location"],
                        "city": loc_info.get("city") or "Remote",
                        "state": loc_info.get("state"),
                        "country": loc_info.get("country", "India"),
                        "remote_type": "remote",
                        "work_modality": "Online",
                        "employment_type": employment_type,
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
                            "parser_version": "2.0-jby-fast",
                            "content_hash": content_hash,
                            "source_timestamp": pub_date,
                            "last_successful_fetch": now_iso
                        }
                    }
                    results.append(canonical_job)
                    if len(results) >= 20:
                        break

        except Exception as e:
            logger.warning(f"Jobicy fetch warning: {e}")

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
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
            returns_structured_salary=True,
            rate_limit_per_minute=60,
            concurrent_limit=3
        )
