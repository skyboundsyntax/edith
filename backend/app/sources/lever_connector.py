"""
Lever Public Postings API Connector.
Uses official public Lever postings endpoint (https://api.lever.co/v0/postings/{company}?mode=json).
Permitted, unauthenticated GET requests according to Lever public API guidelines.
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

LEVER_COMPANIES = [
    {"token": "meesho", "company": "Meesho", "domain": "meesho.com"},
    {"token": "spotify", "company": "Spotify", "domain": "spotify.com"},
    {"token": "eventbrite", "company": "Eventbrite", "domain": "eventbrite.com"},
    {"token": "affirm", "company": "Affirm", "domain": "affirm.com"}
]

class LeverConnector(JobSourceConnector):
    name = "Lever"
    domain = "api.lever.co"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public Postings API: Permitted GET queries for published job listings without auth"
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
        remote_allowed = query_spec.get("remote", False)

        search_tokens = set(keywords + roles + skills)

        async with httpx.AsyncClient(timeout=8.0) as client:
            for comp in LEVER_COMPANIES:
                company_token = comp["token"]
                company_name = comp["company"]
                company_domain = comp["domain"]
                url = f"https://api.lever.co/v0/postings/{company_token}?mode=json"

                try:
                    resp = await client.get(url, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                    if resp.status_code != 200:
                        continue

                    postings = resp.json()
                    if not isinstance(postings, list):
                        continue

                    for item in postings:
                        title = item.get("text", "")
                        title_lower = title.lower()

                        categories = item.get("categories") or {}
                        loc_raw = categories.get("location") or ""
                        loc_lower = loc_raw.lower()
                        team = categories.get("team") or ""
                        commitment = categories.get("commitment") or "Full-time"

                        # 1. Skip non-engineering online gigs
                        if is_online_gig(title, ""):
                            continue

                        # 2. Strict Location check (Drop foreign jobs when searching Pune/Bengaluru/India)
                        loc_matches, loc_pts = matches_location_preference(loc_raw, target_locations, remote_allowed)
                        if not loc_matches or loc_pts == 0:
                            continue

                        # 3. Relevancy check using word boundaries
                        matches_role = False
                        if search_tokens:
                            if any(re.search(r'\b' + re.escape(tok) + r'\b', title_lower) for tok in search_tokens):
                                matches_role = True
                            elif team and any(re.search(r'\b' + re.escape(tok) + r'\b', team.lower()) for tok in search_tokens):
                                matches_role = True
                        else:
                            matches_role = True

                        if not matches_role:
                            continue

                        loc_info = normalize_location(loc_raw)

                        job_id = str(item.get("id"))
                        apply_url = item.get("hostedUrl") or item.get("applyUrl") or f"https://jobs.lever.co/{company_token}/{job_id}"
                        now_iso = datetime.now(timezone.utc).isoformat()
                        created_epoch = item.get("createdAt")
                        if created_epoch:
                            date_posted = datetime.fromtimestamp(created_epoch / 1000, tz=timezone.utc).isoformat()
                        else:
                            date_posted = now_iso

                        raw_str = f"{title}_{company_name}_{job_id}_{loc_raw}"
                        content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                        canonical_job = {
                            "id": f"lev_{company_token}_{job_id}",
                            "source": "lever",
                            "source_job_id": job_id,
                            "source_url": apply_url,
                            "apply_url": apply_url,
                            "title": title,
                            "company": company_name,
                            "company_url": f"https://{company_domain}",
                            "company_domain": company_domain,
                            "description": item.get("descriptionPlain") or f"Role: {title} at {company_name}. Team: {team}. Location: {loc_raw}.",
                            "requirements": [],
                            "responsibilities": [],
                            "skills": [s.title() for s in skills if s in title_lower] or ["Engineering"],
                            "technologies": [],
                            "location": loc_info["canonical_location"],
                            "city": loc_info["city"],
                            "state": loc_info["state"],
                            "country": loc_info["country"],
                            "remote_type": loc_info["remote_type"],
                            "work_modality": "Online" if loc_info["remote_type"] == "remote" else ("Hybrid" if loc_info["remote_type"] == "hybrid" else "Offline"),
                            "employment_type": commitment.lower(),
                            "experience_min": 0,
                            "experience_max": 2 if "intern" in title_lower or "junior" in title_lower else 5,
                            "salary_min": None,
                            "salary_max": None,
                            "salary_currency": "INR",
                            "salary_period": "year",
                            "education": "Degree in Computer Science or related practical experience",
                            "date_posted": date_posted,
                            "date_updated": date_posted,
                            "first_seen_at": now_iso,
                            "last_seen_at": now_iso,
                            "is_active": True,
                            "is_verified": True,
                            "source_timestamp": date_posted,
                            "raw_content_hash": content_hash,
                            "sources": ["lever", "company-careers"],
                            "provenance": {
                                "source_name": "Lever Public Postings API",
                                "source_url": url,
                                "original_job_url": apply_url,
                                "retrieval_timestamp": now_iso,
                                "parser_version": "1.0-lev",
                                "content_hash": content_hash,
                                "source_timestamp": date_posted,
                                "last_successful_fetch": now_iso
                            }
                        }
                        results.append(canonical_job)

                        if len(results) >= 20:
                            break
                except Exception as e:
                    logger.warning(f"Lever fetch error for {company_token}: {e}")
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
                res = await client.get("https://api.lever.co/v0/postings/meesho?mode=json")
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
                        jobs_discovered=len(res.json() if isinstance(res.json(), list) else []),
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
