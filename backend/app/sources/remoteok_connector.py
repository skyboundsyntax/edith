"""
RemoteOK Public Remote Tech Jobs API Connector.
Uses official public API (https://remoteok.com/api).
Permitted public endpoint returning real-time developer, AI/ML, Python, and Full Stack vacancies.
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

class RemoteOKConnector(JobSourceConnector):
    name = "RemoteOK"
    domain = "remoteok.com"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public Developer API: Permitted GET queries for public remote technical vacancies"
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

        url = "https://remoteok.com/api"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0), headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []

                items = resp.json()
                if not isinstance(items, list):
                    return []

                # RemoteOK items include a legal/metadata notice as the first item; filter for dicts with position
                jobs_list = [j for j in items if isinstance(j, dict) and j.get("position")]

                for item in jobs_list:
                    title = item.get("position", "")
                    company = item.get("company", "Tech Company")
                    tags = [t.lower() for t in item.get("tags", [])]
                    loc_raw = item.get("location") or "Worldwide (Remote)"
                    desc_raw = item.get("description", "")

                    # 1. Skip scam online gigs (respect user intent)
                    if is_online_gig(title, desc_raw, query_spec):
                        continue

                    # 2. Check role relevance with flexible matcher
                    if not is_matching_role(title, query_spec, description=" ".join(tags)):
                        continue

                    # 3. Location check
                    effective_loc = f"{loc_raw} (Remote)" if "remote" not in loc_raw.lower() else loc_raw
                    loc_matches, loc_pts = matches_location_preference(effective_loc, target_locations, remote_allowed)
                    if not loc_matches or loc_pts == 0:
                        continue

                    loc_info = normalize_location(effective_loc)
                    job_id = str(item.get("id") or abs(hash(title + company)))
                    apply_url = item.get("url") or f"https://remoteok.com/remote-jobs/{job_id}"
                    now_iso = datetime.now(timezone.utc).isoformat()
                    epoch = item.get("epoch")
                    if epoch:
                        date_posted = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
                    else:
                        date_posted = now_iso

                    raw_str = f"{title}_{company}_{job_id}"
                    content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                    salary_min = None
                    salary_max = None
                    if item.get("salary_min"):
                        try:
                            salary_min = float(item["salary_min"])
                        except (ValueError, TypeError):
                            pass
                    if item.get("salary_max"):
                        try:
                            salary_max = float(item["salary_max"])
                        except (ValueError, TypeError):
                            pass

                    title_lower = title.lower()
                    matched_skills = [s.title() for s in skills if s.lower() in title_lower]
                    if not matched_skills:
                        tag_skills = [t.title() for t in tags[:4] if t.lower() not in ["dev", "engineer", "remote", "job", "jobs"]]
                        matched_skills = tag_skills or ([s.title() for s in skills[:3]] if skills else [title.split()[0].title()])

                    clean_desc = clean_html_snippet(desc_raw)
                    canonical_job = {
                        "id": f"rok_{job_id}",
                        "source": "remoteok",
                        "source_job_id": job_id,
                        "source_url": apply_url,
                        "apply_url": apply_url,
                        "title": title,
                        "company": company,
                        "company_url": f"https://remoteok.com",
                        "company_domain": "remoteok.com",
                        "description": clean_desc[:2500] if clean_desc else f"Remote {title} vacancy at {company}. Skills: {', '.join(tags)}.",
                        "requirements": [],
                        "responsibilities": [],
                        "skills": matched_skills,
                        "technologies": tags[:4],
                        "location": loc_info["canonical_location"],
                        "city": loc_info["city"],
                        "state": loc_info["state"],
                        "country": loc_info["country"],
                        "remote_type": "remote",
                        "work_modality": "Online",
                        "employment_type": "full-time",
                        "experience_min": 0,
                        "experience_max": 3,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "salary_currency": "USD",
                        "salary_period": "year",
                        "education": "Relevant practical software experience",
                        "date_posted": date_posted,
                        "date_updated": date_posted,
                        "first_seen_at": now_iso,
                        "last_seen_at": now_iso,
                        "is_active": True,
                        "is_verified": True,
                        "source_timestamp": date_posted,
                        "raw_content_hash": content_hash,
                        "sources": ["remoteok"],
                        "provenance": {
                            "source_name": "RemoteOK Developer API",
                            "source_url": url,
                            "original_job_url": apply_url,
                            "retrieval_timestamp": now_iso,
                            "parser_version": "1.0-remoteok",
                            "content_hash": content_hash,
                            "source_timestamp": date_posted,
                            "last_successful_fetch": now_iso
                        }
                    }
                    results.append(canonical_job)
                    if len(results) >= 20:
                        break

        except Exception as e:
            logger.warning(f"RemoteOK fetch error: {e}")

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
                res = await client.get("https://remoteok.com/api")
                latency = int((time.time() - start_time) * 1000)
                if res.status_code == 200:
                    items = [j for j in res.json() if isinstance(j, dict) and j.get("position")]
                    return SourceHealth(
                        name=self.name,
                        domain=self.domain,
                        status="ONLINE",
                        access_method=self.access_method,
                        permission_status=self.permission_status,
                        robots_policy=self.robots_policy,
                        rate_limit=self.rate_limit,
                        latency_ms=latency,
                        jobs_discovered=len(items),
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
