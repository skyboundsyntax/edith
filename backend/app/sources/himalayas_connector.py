"""
Himalayas Public Remote Tech Jobs API Connector.
Uses official public Himalayas API (https://himalayas.app/jobs/api).
Permitted public endpoint returning real-time developer, AI, software engineering, and systems jobs.
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

class HimalayasConnector(JobSourceConnector):
    name = "Himalayas"
    domain = "himalayas.app"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public API: Permitted GET queries for remote technical opportunities"
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

        url = "https://himalayas.app/jobs/api?limit=30"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0), headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                jobs_list = data.get("jobs", [])

                for item in jobs_list:
                    title = item.get("title", "")
                    company = item.get("companyName", "Tech Company")
                    categories = [c.lower() for c in item.get("categories", [])]
                    loc_restrictions = item.get("locationRestrictions") or []
                    loc_raw = ", ".join(loc_restrictions) if loc_restrictions else "Worldwide (Remote)"
                    desc_raw = item.get("description", "") or item.get("excerpt", "")

                    # 1. Skip non-engineering online gigs
                    if is_online_gig(title, desc_raw):
                        continue

                    # 2. Check role relevance with flexible matcher
                    if not is_matching_role(title, query_spec, description=" ".join(categories)):
                        continue

                    # 3. Location check
                    effective_loc = f"{loc_raw} (Remote)" if "remote" not in loc_raw.lower() else loc_raw
                    loc_matches, loc_pts = matches_location_preference(effective_loc, target_locations, remote_allowed)
                    if not loc_matches or loc_pts == 0:
                        continue

                    loc_info = normalize_location(effective_loc)
                    job_id = str(item.get("guid") or abs(hash(title + company)))
                    apply_url = item.get("applicationLink") or f"https://himalayas.app/jobs/{job_id}"
                    now_iso = datetime.now(timezone.utc).isoformat()
                    pub_date = item.get("pubDate") or now_iso

                    raw_str = f"{title}_{company}_{job_id}"
                    content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                    salary_min = None
                    salary_max = None
                    if item.get("minSalary"):
                        try:
                            salary_min = float(item["minSalary"])
                        except (ValueError, TypeError):
                            pass
                    if item.get("maxSalary"):
                        try:
                            salary_max = float(item["maxSalary"])
                        except (ValueError, TypeError):
                            pass

                    title_lower = title.lower()
                    matched_skills = [s.title() for s in skills if s.lower() in title_lower]
                    if not matched_skills:
                        matched_skills = [c.title() for c in categories[:4] if c not in ["software engineering", "engineering"]] or ["Software Engineering"]

                    clean_desc = clean_html_snippet(desc_raw)
                    canonical_job = {
                        "id": f"him_{job_id[:24]}",
                        "source": "himalayas",
                        "source_job_id": job_id,
                        "source_url": apply_url,
                        "apply_url": apply_url,
                        "title": title,
                        "company": company,
                        "company_url": f"https://himalayas.app/companies/{item.get('companySlug', company.lower())}",
                        "company_domain": "himalayas.app",
                        "description": clean_desc[:2500] if clean_desc else f"Remote {title} opportunity at {company}.",
                        "requirements": [],
                        "responsibilities": [],
                        "skills": matched_skills,
                        "technologies": categories[:4],
                        "location": loc_info["canonical_location"],
                        "city": loc_info["city"],
                        "state": loc_info["state"],
                        "country": loc_info["country"],
                        "remote_type": "remote",
                        "work_modality": "Online",
                        "employment_type": (item.get("employmentType") or "full-time").lower(),
                        "experience_min": 0,
                        "experience_max": 3,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "salary_currency": item.get("currency") or "USD",
                        "salary_period": item.get("salaryPeriod") or "year",
                        "education": "Relevant software engineering experience",
                        "date_posted": pub_date,
                        "date_updated": pub_date,
                        "first_seen_at": now_iso,
                        "last_seen_at": now_iso,
                        "is_active": True,
                        "is_verified": True,
                        "source_timestamp": pub_date,
                        "raw_content_hash": content_hash,
                        "sources": ["himalayas"],
                        "provenance": {
                            "source_name": "Himalayas Public API",
                            "source_url": url,
                            "original_job_url": apply_url,
                            "retrieval_timestamp": now_iso,
                            "parser_version": "1.0-himalayas",
                            "content_hash": content_hash,
                            "source_timestamp": pub_date,
                            "last_successful_fetch": now_iso
                        }
                    }
                    results.append(canonical_job)
                    if len(results) >= 20:
                        break

        except Exception as e:
            logger.warning(f"Himalayas fetch error: {e}")

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
                res = await client.get("https://himalayas.app/jobs/api?limit=2")
                latency = int((time.time() - start_time) * 1000)
                if res.status_code == 200:
                    items = res.json().get("jobs", [])
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
