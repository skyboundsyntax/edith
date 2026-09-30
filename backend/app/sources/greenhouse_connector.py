"""
Greenhouse Public Job Board API Connector.
Uses official public endpoints (https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true).
Permitted, unauthenticated GET requests according to Greenhouse API terms.
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

logger = logging.getLogger(__name__)

# Curated active tech companies with public Greenhouse boards that hire in India / Remote
GREENHOUSE_COMPANIES = [
    {"token": "inmobi", "company": "InMobi", "domain": "inmobi.com"},
    {"token": "rubrik", "company": "Rubrik", "domain": "rubrik.com"},
    {"token": "mongodb", "company": "MongoDB", "domain": "mongodb.com"},
    {"token": "databricks", "company": "Databricks", "domain": "databricks.com"},
    {"token": "cloudflare", "company": "Cloudflare", "domain": "cloudflare.com"},
    {"token": "elastic", "company": "Elastic", "domain": "elastic.co"},
    {"token": "stripe", "company": "Stripe", "domain": "stripe.com"},
    {"token": "gitlab", "company": "GitLab", "domain": "gitlab.com"},
    {"token": "figma", "company": "Figma", "domain": "figma.com"},
    {"token": "hackerrank", "company": "HackerRank", "domain": "hackerrank.com"},
    {"token": "okta", "company": "Okta", "domain": "okta.com"},
    {"token": "coinbase", "company": "Coinbase", "domain": "coinbase.com"},
    {"token": "airbnb", "company": "Airbnb", "domain": "airbnb.com"},
    {"token": "twilio", "company": "Twilio", "domain": "twilio.com"}
]

class GreenhouseConnector(JobSourceConnector):
    name = "Greenhouse"
    domain = "boards-api.greenhouse.io"
    access_method = "PUBLIC_API"
    permission_status = "PERMITTED"
    robots_policy = "Public Board API: Permitted GET queries for published job listings without auth"
    rate_limit = "60 requests/min"
    enabled = True

    def can_handle(self, query_spec: Dict[str, Any]) -> bool:
        # Greenhouse handles tech, engineering, AI/ML and product companies
        return True

    async def search(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Queries public Greenhouse boards of participating tech companies in parallel.
        Filters by query keywords, roles, and location.
        """
        results = []
        keywords = [k.lower() for k in (query_spec.get("keywords") or [])]
        roles = [r.lower() for r in (query_spec.get("roles") or [])]
        skills = [s.lower() for s in (query_spec.get("skills") or [])]
        target_locations = [l.lower() for l in (query_spec.get("locations") or [])]
        remote_allowed = query_spec.get("remote", False)

        search_tokens = set(keywords + roles + skills)
        role_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(tok) for tok in search_tokens) + r')\b', re.IGNORECASE) if search_tokens else None

        async def fetch_company_jobs(client: httpx.AsyncClient, comp: Dict[str, str]) -> List[Dict[str, Any]]:
            board_token = comp["token"]
            company_name = comp["company"]
            company_domain = comp["domain"]
            url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=false"
            comp_jobs = []

            try:
                resp = await client.get(url, headers={"User-Agent": "EDITH-JobIntelligence/1.0"})
                if resp.status_code != 200:
                    return []
                
                data = resp.json()
                jobs_list = data.get("jobs", [])

                for item in jobs_list:
                    title = item.get("title", "")
                    title_lower = title.lower()

                    # 1. Relevancy check: title or department matches target keywords/roles
                    if role_pattern:
                        if not role_pattern.search(title_lower):
                            departments = item.get("departments", [])
                            dept_name = departments[0].get("name", "").lower() if departments else ""
                            if not role_pattern.search(dept_name):
                                continue

                    # 2. Skip non-engineering online gigs
                    if is_online_gig(title, ""):
                        continue

                    # 3. Strict Location check (Drop foreign jobs when searching Pune/Bengaluru/India)
                    loc_raw = (item.get("location") or {}).get("name", "")
                    loc_matches, loc_pts = matches_location_preference(loc_raw, target_locations, remote_allowed)
                    if not loc_matches or loc_pts == 0:
                        continue

                    loc_info = normalize_location(loc_raw)

                    job_id = str(item.get("id"))
                    apply_url = item.get("absolute_url") or f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}"
                    now_iso = datetime.now(timezone.utc).isoformat()
                    updated_at = item.get("updated_at") or now_iso

                    raw_str = f"{title}_{company_name}_{job_id}_{loc_raw}"
                    content_hash = hashlib.sha256(raw_str.encode()).hexdigest()

                    canonical_job = {
                        "id": f"gh_{board_token}_{job_id}",
                        "source": "greenhouse",
                        "source_job_id": job_id,
                        "source_url": apply_url,
                        "apply_url": apply_url,
                        "title": title,
                        "company": company_name,
                        "company_url": f"https://{company_domain}",
                        "company_domain": company_domain,
                        "description": f"Role: {title} at {company_name}. Department: {item.get('departments', [{}])[0].get('name', 'Engineering')}. Location: {loc_raw}.",
                        "requirements": [],
                        "responsibilities": [],
                        "skills": [s.title() for s in skills if s in title_lower] or ["Software Development"],
                        "technologies": [],
                        "location": loc_info["canonical_location"],
                        "city": loc_info["city"],
                        "state": loc_info["state"],
                        "country": loc_info["country"],
                        "remote_type": loc_info["remote_type"],
                        "work_modality": "Online" if loc_info["remote_type"] == "remote" else "Offline",
                        "employment_type": "full-time",
                        "experience_min": 0,
                        "experience_max": 2 if "intern" in title_lower or "junior" in title_lower else 5,
                        "salary_min": None,
                        "salary_max": None,
                        "salary_currency": "INR",
                        "salary_period": "year",
                        "education": "Degree in Computer Science, Engineering, or related technical field",
                        "date_posted": updated_at,
                        "date_updated": updated_at,
                        "first_seen_at": now_iso,
                        "last_seen_at": now_iso,
                        "is_active": True,
                        "is_verified": True,
                        "source_timestamp": updated_at,
                        "raw_content_hash": content_hash,
                        "sources": ["greenhouse", "company-careers"],
                        "provenance": {
                            "source_name": "Greenhouse Public Job Board API",
                            "source_url": url,
                            "original_job_url": apply_url,
                            "retrieval_timestamp": now_iso,
                            "parser_version": "1.0-gh",
                            "content_hash": content_hash,
                            "source_timestamp": updated_at,
                            "last_successful_fetch": now_iso
                        }
                    }
                    comp_jobs.append(canonical_job)
                    if len(comp_jobs) >= 8:
                        break
                return comp_jobs
            except Exception as e:
                logger.warning(f"Greenhouse board fetch error for {board_token}: {e}")
                return []

        async with httpx.AsyncClient(timeout=6.0, limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)) as client:
            tasks = [fetch_company_jobs(client, comp) for comp in GREENHOUSE_COMPANIES]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in batch_results:
                if isinstance(res, list):
                    results.extend(res)

        return results

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        # Individual job lookup can parse boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}
        return None

    async def health_check(self) -> SourceHealth:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://boards-api.greenhouse.io/v1/boards/inmobi/jobs?content=false")
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
        except Exception as e:
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
