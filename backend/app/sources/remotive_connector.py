"""
Remotive Developer Jobs API Connector.
Uses official public Remotive API (https://remotive.com/api/remote-jobs).
Permitted public endpoint returning real-time developer, AI, Python, and frontend/backend vacancies.
"""
import time
import httpx
import logging
import hashlib
import urllib.parse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import re

from backend.app.sources.base import JobSourceConnector, SourceHealth, SourceCapabilities
from backend.app.locations.india_locations import normalize_location, matches_location_preference, is_online_gig
from backend.app.intelligence.role_matcher import is_matching_role

logger = logging.getLogger(__name__)

class RemotiveConnector(JobSourceConnector):
    name = "Remotive"
    domain = "remotive.com"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public API: Permitted GET queries for remote tech job listings"
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
        roles = query_spec.get("roles") or []

        search_term = "software"
        if skills:
            search_term = skills[0]
        elif roles:
            search_term = roles[0].split()[0]

        url = f"https://remotive.com/api/remote-jobs?search={urllib.parse.quote_plus(search_term)}&limit=25"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0)) as client:
                resp = await client.get(url, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                if resp.status_code != 200:
                    return []

                data = resp.json()
                items = data.get("jobs", [])

                for item in items:
                    title = item.get("title", "")
                    company = item.get("company_name", "Tech Startup")
                    job_url = item.get("url", "")
                    raw_desc = item.get("description", "")
                    clean_desc = BeautifulSoup(raw_desc, "html.parser").get_text(separator="\n", strip=True) if raw_desc else ""
                    candidate_loc = item.get("candidate_required_location") or "Worldwide"

                    # 1. Skip non-engineering online gigs
                    if is_online_gig(title, clean_desc):
                        continue

                    # 2. Check role relevance with flexible matcher
                    if not is_matching_role(title, query_spec, description=clean_desc):
                        continue

                    # 3. Location matching
                    effective_loc = f"{candidate_loc} (Remote)" if "remote" not in candidate_loc.lower() else candidate_loc
                    loc_matches, loc_pts = matches_location_preference(effective_loc, target_locations, remote_allowed)
                    if not loc_matches or loc_pts == 0:
                        continue

                    loc_info = normalize_location(effective_loc)
                    salary = item.get("salary") or "Not Disclosed"
                    job_id = str(item.get("id"))
                    now_iso = datetime.now(timezone.utc).isoformat()
                    pub_date = item.get("publication_date") or now_iso

                    content_hash = hashlib.sha256(f"{title}_{company}_{job_id}".encode()).hexdigest()

                    title_lower = title.lower()
                    matched_skills = [s.title() for s in skills if s.lower() in title_lower]
                    if not matched_skills:
                        matched_skills = [s.title() for s in item.get("tags", [])][:4] or ["Python", "Engineering"]

                    canonical_job = {
                        "id": f"rem_{job_id}",
                        "source": "remotive",
                        "source_job_id": job_id,
                        "source_url": job_url,
                        "apply_url": job_url,
                        "title": title,
                        "company": company,
                        "company_url": f"https://remotive.com/remote-companies/{urllib.parse.quote(company.lower().replace(' ', '-'))}",
                        "company_domain": "remotive.com",
                        "description": clean_desc[:2500] if clean_desc else f"Remote {title} vacancy at {company}.",
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
                        "employment_type": item.get("job_type", "full-time").lower(),
                        "experience_min": query_spec.get("experience_min", 0),
                        "experience_max": query_spec.get("experience_max", 3),
                        "salary_min": None,
                        "salary_max": None,
                        "salary_currency": "USD" if "$" in salary else "INR",
                        "salary_period": "year",
                        "education": query_spec.get("education_level"),
                        "date_posted": pub_date,
                        "date_updated": pub_date,
                        "first_seen_at": now_iso,
                        "last_seen_at": now_iso,
                        "is_active": True,
                        "is_verified": True,
                        "is_link_out": False,
                        "source_timestamp": pub_date,
                        "raw_content_hash": content_hash,
                        "sources": ["remotive"],
                        "provenance": {
                            "source_name": "Remotive Remote Jobs",
                            "source_url": job_url,
                            "original_job_url": job_url,
                            "retrieval_timestamp": now_iso,
                            "parser_version": "2.0-remotive-fast",
                            "content_hash": content_hash,
                            "source_timestamp": pub_date,
                            "last_successful_fetch": now_iso
                        }
                    }
                    results.append(canonical_job)
                    if len(results) >= 20:
                        break

        except Exception as e:
            logger.error(f"Remotive connector error: {e}")

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        t0 = time.time()
        status = "ONLINE"
        jobs_discovered = 0
        latency = 0
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get("https://remotive.com/api/remote-jobs?limit=5")
                latency = int((time.time() - t0) * 1000)
                if resp.status_code == 200:
                    jobs_discovered = len(resp.json().get("jobs", []))
                else:
                    status = "DEGRADED"
        except Exception:
            status = "DEGRADED"
            latency = int((time.time() - t0) * 1000)

        return SourceHealth(
            name=self.name,
            domain=self.domain,
            status=status,
            access_method=self.access_method,
            permission_status=self.permission_status,
            robots_policy=self.robots_policy,
            rate_limit=self.rate_limit,
            latency_ms=latency,
            jobs_discovered=jobs_discovered,
            error_count=0,
            enabled=True
        )

    def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_keyword_search=True,
            supports_location_filter=False,
            supports_experience_filter=False,
            supports_remote_filter=True,
            returns_structured_salary=True,
            rate_limit_per_minute=60,
            concurrent_limit=3
        )
