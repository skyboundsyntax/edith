"""
Link-Out Search Connectors for External Platforms (Naukri, Indeed).
Strictly adheres to user requirements:
- NEVER generates fake placeholder or 'Explore...' job records.
- Only real job postings are returned.
"""
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
        self.robots_policy = f"Platform restricts automated data collection. EDITH does not generate mock or placeholder listings."
        self.rate_limit = "Unlimited (Client-Side Navigation)"
        self.enabled = True

    def can_handle(self, query_spec: Dict[str, Any]) -> bool:
        return False

    async def search(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Never generate mock or placeholder 'Explore...' records.
        Returns an empty list so only 100% genuine live scraped jobs are surfaced.
        """
        return []

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
            supports_keyword_search=False,
            supports_location_filter=False,
            supports_experience_filter=False,
            supports_remote_filter=False,
            returns_structured_salary=False,
            rate_limit_per_minute=9999,
            concurrent_limit=10
        )
