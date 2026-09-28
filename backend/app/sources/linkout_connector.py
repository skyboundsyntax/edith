"""
Link-Out Search Connectors for Restricted Platforms (LinkedIn, Indeed, Naukri).
Strictly adheres to Legal / Source Policy:
- Does NOT scrape logged-in pages or evade anti-bot / CAPTCHA defenses.
- Transparently generates deep-link queries for live search on destination platforms.
- Clearly flagged in UI as LINK-OUT SOURCE (Never disguised as scraped data).
"""
import urllib.parse
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from backend.app.sources.base import JobSourceConnector, SourceHealth, SourceCapabilities

class LinkOutPlatformConnector(JobSourceConnector):
    def __init__(self, platform_name: str, domain: str, base_url_template: str):
        self.name = platform_name
        self.domain = domain
        self.base_url_template = base_url_template
        self.access_method = "LINK_OUT_ONLY"
        self.permission_status = "LINK_OUT_ONLY"
        self.robots_policy = f"Platform restricts automated data collection. EDITH generates transparent, direct link-out search navigation."
        self.rate_limit = "Unlimited (Client-Side Navigation)"
        self.enabled = True

    def can_handle(self, query_spec: Dict[str, Any]) -> bool:
        return True

    async def search(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates genuine link-out targets tailored specifically to the user's role, skills, and target locations.
        """
        keywords = " ".join((query_spec.get("roles") or [])[:2] + (query_spec.get("skills") or [])[:2] + (query_spec.get("keywords") or [])[:2]).strip()
        if not keywords:
            keywords = "Software Engineer Python"

        locations = query_spec.get("locations") or []
        location_str = locations[0] if locations else ("Remote" if query_spec.get("remote") else "India")

        encoded_kw = urllib.parse.quote_plus(keywords)
        encoded_loc = urllib.parse.quote_plus(location_str)

        if "linkedin" in self.domain:
            target_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_kw}&location={encoded_loc}&sortBy=DD"
        elif "indeed" in self.domain:
            target_url = f"https://in.indeed.com/jobs?q={encoded_kw}&l={encoded_loc}&sort=date"
        elif "naukri" in self.domain:
            # Naukri query URL format
            clean_kw = keywords.lower().replace(' ', '-')
            clean_loc = location_str.lower().replace(' ', '-')
            target_url = f"https://www.naukri.com/{clean_kw}-jobs-in-{clean_loc}"
        else:
            target_url = f"https://{self.domain}/search?q={encoded_kw}"

        now_iso = datetime.now(timezone.utc).isoformat()

        # Notice: Returns a clearly marked LINK_OUT record, NOT a fake scraped job!
        return [{
            "id": f"linkout_{self.name.lower()}",
            "source": self.name.lower(),
            "source_job_id": "search_portal",
            "source_url": target_url,
            "apply_url": target_url,
            "title": f"Explore '{keywords}' Roles on {self.name}",
            "company": f"{self.name} Live Job Search",
            "company_url": f"https://{self.domain}",
            "company_domain": self.domain,
            "description": f"Direct link-out search for {keywords} in {location_str} on {self.name}. Restricted from unauthorized scraping by platform policy.",
            "requirements": [],
            "responsibilities": [],
            "skills": [s.title() for s in (query_spec.get("skills") or [])],
            "technologies": [],
            "location": location_str,
            "city": location_str if location_str != "Remote" else None,
            "state": None,
            "country": "India",
            "remote_type": "remote" if query_spec.get("remote") else "on-site",
            "employment_type": "full-time",
            "experience_min": query_spec.get("experience_min"),
            "experience_max": query_spec.get("experience_max"),
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "INR",
            "salary_period": "year",
            "education": None,
            "date_posted": now_iso,
            "date_updated": now_iso,
            "first_seen_at": now_iso,
            "last_seen_at": now_iso,
            "is_active": True,
            "is_verified": False,
            "is_link_out": True,  # Explicit flag for frontend
            "source_timestamp": now_iso,
            "raw_content_hash": "link_out_portal",
            "sources": [self.name.lower()],
            "provenance": {
                "source_name": f"{self.name} (Link-Out Only)",
                "source_url": target_url,
                "original_job_url": target_url,
                "retrieval_timestamp": now_iso,
                "parser_version": "1.0-linkout",
                "content_hash": "linkout",
                "source_timestamp": now_iso,
                "last_successful_fetch": now_iso
            }
        }]

    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        return None

    async def health_check(self) -> SourceHealth:
        return SourceHealth(
            name=self.name,
            domain=self.domain,
            status="LINK_OUT_ONLY",
            access_method=self.access_method,
            permission_status=self.permission_status,
            robots_policy=self.robots_policy,
            rate_limit=self.rate_limit,
            latency_ms=10,
            jobs_discovered=0,
            error_count=0,
            enabled=True
        )

    def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_keyword_search=True,
            supports_location_filter=True,
            supports_experience_filter=True,
            supports_remote_filter=True,
            returns_structured_salary=False,
            rate_limit_per_minute=9999,
            concurrent_limit=10
        )
