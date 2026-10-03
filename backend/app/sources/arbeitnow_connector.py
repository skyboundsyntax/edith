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
import html
import urllib.parse
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
    clean = re.sub(r'Find\s+Jobs\s+in\s+[^.]*\s+on\s+Arbeitnow', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'Apply\s+(now\s+)?on\s+Arbeitnow', '', clean, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', clean).strip()

class ArbeitnowConnector(JobSourceConnector):
    name = "Arbeitnow"
    domain = "arbeitnow.com"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public Job Board API: Permitted GET queries for public technical job postings"
    rate_limit = "60 requests/min"
    enabled = True

    def can_handle(self, query_spec: Dict[str, Any]) -> bool:
        keywords = [k.lower() for k in (query_spec.get("keywords") or [])]
        if any("on-site only" in k or "onsite only" in k or "offline only" in k for k in keywords):
            locations = [l.lower().strip() for l in (query_spec.get("locations") or [])]
            indian_hubs = ["pune", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad", "chennai", "noida", "gurgaon", "india"]
            if any(any(h in loc for h in indian_hubs) for loc in locations):
                return False
        return True

    async def search(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        target_locations = [l.lower() for l in (query_spec.get("locations") or [])]
        remote_allowed = query_spec.get("remote", False) or not any(l in ["on-site", "offline"] for l in target_locations)
        skills = query_spec.get("skills") or []

        roles = query_spec.get("roles") or []
        skills = query_spec.get("skills") or []
        keywords = query_spec.get("keywords") or []
        raw_prompt = (query_spec.get("raw_prompt") or "").strip()

        search_kw = ""
        if skills:
            search_kw = skills[0]
        elif roles:
            search_kw = roles[0].split()[0]
        elif keywords:
            search_kw = keywords[0]
        elif raw_prompt:
            search_kw = raw_prompt.split()[0]

        if search_kw:
            url = f"https://www.arbeitnow.com/api/job-board-api?search={urllib.parse.quote_plus(search_kw)}"
        else:
            url = "https://www.arbeitnow.com/api/job-board-api"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0)) as client:
                resp = await client.get(url, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                if resp.status_code != 200:
                    return []

                data = resp.json()
                items = data.get("data", [])

                for item in items:
                    title = item.get("title", "")
                    company = item.get("company_name", "Tech Startup")
                    loc_raw = item.get("location", "")
                    is_remote = item.get("remote", False)
                    tags = [t.lower() for t in item.get("tags", [])]
                    desc_raw = item.get("description", "")

                    # 1. Skip scam online gigs (respect user intent)
                    if is_online_gig(title, desc_raw, query_spec):
                        continue

                    # 2. Check role relevance with flexible matcher
                    if not is_matching_role(title, query_spec, description=" ".join(tags)):
                        continue

                    # 3. Location check
                    effective_loc = "Remote" if is_remote else loc_raw
                    loc_matches, loc_pts = matches_location_preference(effective_loc, target_locations, remote_allowed)
                    if not loc_matches or loc_pts == 0:
                        continue

                    loc_info = normalize_location(effective_loc)
                    job_id = item.get("slug") or str(abs(hash(title + company)))
                    apply_url = item.get("url") or f"https://www.arbeitnow.com/jobs/{job_id}"
                    now_iso = datetime.now(timezone.utc).isoformat()
                    created_epoch = item.get("created_at")
                    if created_epoch:
                        date_posted = datetime.fromtimestamp(created_epoch, tz=timezone.utc).isoformat()
                    else:
                        date_posted = now_iso

                    raw_str = f"{title}_{company}_{job_id}"
                    content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                    title_lower = title.lower()
                    matched_skills = [s.title() for s in skills if s.lower() in title_lower]
                    if not matched_skills:
                        matched_skills = [t.title() for t in tags[:4] if t.lower() not in ["jobs", "job", "remote"]] or ([s.title() for s in skills[:3]] if skills else [title.split()[0].title()])

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
                        "description": clean_html_snippet(item.get("description")) or f"Role: {title} at {company}. Tags: {', '.join(tags)}.",
                        "requirements": [],
                        "responsibilities": [],
                        "skills": matched_skills,
                        "technologies": tags[:4],
                        "location": loc_info["canonical_location"],
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
                            "parser_version": "2.0-abn-fast",
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
            async with httpx.AsyncClient(timeout=3.0) as client:
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
