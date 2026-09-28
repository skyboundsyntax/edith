"""
Base classes and interfaces for EDITH Job Source Connectors.
Strictly adheres to Legal / Source Policy:
- No CAPTCHA bypass
- No login wall / paywall circumvention
- No fake accounts or stolen tokens
- Source-aware access methods and rate limits
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class SourceHealth(BaseModel):
    name: str
    domain: str
    status: str  # ONLINE, LINK_OUT_ONLY, DEGRADED, UNAVAILABLE
    access_method: str  # PUBLIC_API, PUBLIC_FEED, PUBLIC_CAREER_PAGE, AUTHORIZED_API, USER_PROVIDED_URL, LINK_OUT_ONLY
    permission_status: str  # PERMITTED, RESTRICTED, LINK_OUT_ONLY
    robots_policy: str
    rate_limit: str
    last_checked: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: int = 0
    jobs_discovered: int = 0
    error_count: int = 0
    enabled: bool = True

class SourceCapabilities(BaseModel):
    supports_keyword_search: bool = True
    supports_location_filter: bool = True
    supports_experience_filter: bool = False
    supports_remote_filter: bool = True
    returns_structured_salary: bool = False
    rate_limit_per_minute: int = 60
    concurrent_limit: int = 3

class JobSourceConnector(ABC):
    """
    Standard interface implemented by all EDITH source connectors.
    """
    name: str
    domain: str
    access_method: str
    permission_status: str
    robots_policy: str
    rate_limit: str = "60/min"
    enabled: bool = True

    @abstractmethod
    def can_handle(self, query_spec: Dict[str, Any]) -> bool:
        """Determines if this source is applicable for the query."""
        pass

    @abstractmethod
    async def search(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Executes search against permitted endpoint and returns raw/normalized job dicts."""
        pass

    @abstractmethod
    async def get_job(self, source_job_id_or_url: str) -> Optional[Dict[str, Any]]:
        """Fetches individual job details if supported."""
        pass

    @abstractmethod
    async def health_check(self) -> SourceHealth:
        """Verifies endpoint connectivity and returns health status."""
        pass

    @abstractmethod
    def get_capabilities(self) -> SourceCapabilities:
        """Returns feature capabilities of the connector."""
        pass
