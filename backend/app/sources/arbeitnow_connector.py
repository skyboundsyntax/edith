"""
Arbeitnow Public Developer Jobs API Connector.
Uses official public Arbeitnow API (https://www.arbeitnow.com/api/job-board-api).
Permitted public endpoint returning developer, AI, and Python opportunities.
"""
import time
import httpx
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import re

from backend.app.sources.base import JobSourceConnector, SourceHealth, SourceCapabilities
from backend.app.locations.india_locations import normalize_location, matches_location_preference, is_online_gig

logger = logging.getLogger(__name__)

class ArbeitnowConnector(JobSourceConnector):
    name = "Arbeitnow"
    domain = "arbeitnow.com"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public Job Board API: Permitted GET queries for public technical job postings"
    rate_limit = "60 requests/min"
    enabled = True

    def can_handle(self, query_spec: Dict[str, Any]) -> bool:
        locations = query_spec.get("locations") or []
        remote = query_spec.get("remote", False)
        # If user explicitly wants on-site local jobs in India, skip EU board
        if locations and not remote:
            return False
        return True

    async def search(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        keywords = [k.lower() for k in (query_spec.get("keywords") or [])]
        roles = [r.lower() for r in (query_spec.get("roles") or [])]
        skills = [s.lower() for s in (query_spec.get("skills") or [])]
        target_locations = [l.lower() for l in (query_spec.get("locations") or [])]
        remote_allowed = query_spec.get("remote", False)

        search_tokens = set(keywords + roles + skills)

        url = "https://www.arbeitnow.com/api/job-board-api"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                if resp.status_code != 200:
                    return []

                data = resp.json()
                items = data.get("data", [])

                for item in items:
                    title = item.get("title", "")
                    title_lower = title.lower()
                    company = item.get("company_name", "Tech Startup")
                    loc_raw = item.get("location", "")
                    loc_lower = loc_raw.lower()
                    is_remote = item.get("remote", False)
                    tags = [t.lower() for t in item.get("tags", [])]
                    desc_raw = item.get("description", "")

                    # 1. Skip non-engineering online gigs
                    if is_online_gig(title, desc_raw):
                        continue

                    # 2. Strict Location check (Drop European/German on-site or geo-restricted jobs for India queries)
                    loc_matches, loc_pts = matches_location_preference(loc_raw, target_locations, remote_allowed)
                    if not loc_matches or loc_pts == 0:
                        continue

                    # 3. Relevancy check using word boundaries (avoids 'ai' matching 'trainer', 'trainee', 'spain', etc.)
                    matches_role = False
                    if search_tokens:
                        if any(re.search(r'\b' + re.escape(tok) + r'\b', title_lower) for tok in search_tokens):
                            matches_role = True
                        else:
                            tags_text = " ".join(tags)
                            if any(re.search(r'\b' + re.escape(tok) + r'\b', tags_text) for tok in search_tokens):
                                matches_role = True
                    else:
                        matches_role = True

                    if not matches_role:
                        continue

                    loc_info = normalize_location(loc_raw)
                    if is_remote:
                        loc_info["remote_type"] = "remote"

                    job_id = item.get("slug") or str(hash(title + company))
                    apply_url = item.get("url") or f"https://www.arbeitnow.com/jobs/{job_id}"
                    now_iso = datetime.now(timezone.utc).isoformat()
                    created_epoch = item.get("created_at")
                    if created_epoch:
                        date_posted = datetime.fromtimestamp(created_epoch, tz=timezone.utc).isoformat()
                    else:
                        date_posted = now_iso

                    raw_str = f"{title}_{company}_{job_id}"
                    content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                    canonical_job = {
                        "id": f"abn_{job_id[:24]}",
                        "source": "arbeitnow",
                        "source_job_id": job_id,
                        "source_url": apply_url,
                        "apply_url": apply_url,
                        "title": title,
                        "company": company,
                        "company_url": f"https://www.arbeitnow.com/company/{company.lower().replace(' ', '-')}",
                        "company_domain": "arbeitnow.com",
                        "description": item.get("description") or f"Role: {title} at {company}. Tags: {', '.join(tags)}.",
                        "requirements": [],
                        "responsibilities": [],
                        "skills": [t.title() for t in tags[:5]] or ["Software Development"],
                        "technologies": tags[:4],
                        "location": f"{loc_raw} (Remote)" if is_remote else loc_info["canonical_location"],
                        "city": loc_info["city"],
                        "state": loc_info["state"],
                        "country": loc_info["country"],
                        "remote_type": "remote" if is_remote else loc_info["remote_type"],
                        "work_modality": "Online" if (is_remote or loc_info["remote_type"] == "remote") else "Offline",
                        "employment_type": "full-time",
                        "experience_min": 0,
                        "experience_max": 3,
                        "salary_min": None,
                        "salary_max": None,
                        "salary_currency": "EUR",
                        "salary_period": "year",
                        "education": "Relevant practical experience",
                        "date_posted": date_posted,
                        "date_updated": date_posted,
                        "first_seen_at": now_iso,
                        "last_seen_at": now_iso,
                        "is_active": True,
                        "is_verified": True,
                        "source_timestamp": date_posted,
                        "raw_content_hash": content_hash,
                        "sources": ["arbeitnow"],
                        "provenance": {
                            "source_name": "Arbeitnow Public API",
                            "source_url": url,
                            "original_job_url": apply_url,
                            "retrieval_timestamp": now_iso,
                            "parser_version": "1.0-abn",
                            "content_hash": content_hash,
                            "source_timestamp": date_posted,
                            "last_successful_fetch": now_iso
                        }
                    }
                    results.append(canonical_job)

                    if len(results) >= 20:
                        break

        except Exception as e:
            logger.warning(f"Arbeitnow fetch error: {e}")

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://www.arbeitnow.com/api/job-board-api")
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
                        jobs_discovered=len(res.json().get("data", [])),
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
