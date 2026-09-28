"""
Source Policy Registry for EDITH.
Tracks and orchestrates all permitted job source connectors:
- Greenhouse
- Lever
- Ashby
- Jobicy
- Arbeitnow
- LinkOut (LinkedIn, Indeed, Naukri)
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from backend.app.sources.base import JobSourceConnector, SourceHealth
from backend.app.sources.greenhouse_connector import GreenhouseConnector
from backend.app.sources.lever_connector import LeverConnector
from backend.app.sources.ashby_connector import AshbyConnector
from backend.app.sources.jobicy_connector import JobicyConnector
from backend.app.sources.arbeitnow_connector import ArbeitnowConnector
from backend.app.sources.linkout_connector import LinkOutPlatformConnector

logger = logging.getLogger(__name__)

class SourcePolicyRegistry:
    def __init__(self):
        self.connectors: Dict[str, JobSourceConnector] = {
            "greenhouse": GreenhouseConnector(),
            "lever": LeverConnector(),
            "ashby": AshbyConnector(),
            "jobicy": JobicyConnector(),
            "arbeitnow": ArbeitnowConnector(),
            "linkedin": LinkOutPlatformConnector("LinkedIn", "linkedin.com", "https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}"),
            "indeed": LinkOutPlatformConnector("Indeed", "in.indeed.com", "https://in.indeed.com/jobs?q={keywords}&l={location}"),
            "naukri": LinkOutPlatformConnector("Naukri", "naukri.com", "https://www.naukri.com/{keywords}-jobs-in-{location}")
        }
        self.health_cache: Dict[str, SourceHealth] = {}
        self.last_health_check: Optional[datetime] = None

    def get_connector(self, name: str) -> Optional[JobSourceConnector]:
        return self.connectors.get(name.lower())

    def get_live_connectors(self) -> List[JobSourceConnector]:
        """Returns connectors with automated fetching capabilities."""
        return [c for c in self.connectors.values() if c.access_method in ["PUBLIC_API", "PUBLIC_FEED", "PUBLIC_CAREER_PAGE"] and c.enabled]

    def get_linkout_connectors(self) -> List[JobSourceConnector]:
        """Returns restricted platforms treated as link-out only."""
        return [c for c in self.connectors.values() if c.access_method == "LINK_OUT_ONLY" and c.enabled]

    async def check_all_health(self) -> Dict[str, SourceHealth]:
        """Runs parallel health checks on all registered connectors."""
        tasks = []
        names = []
        for name, connector in self.connectors.items():
            names.append(name)
            tasks.append(connector.health_check())

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, res in zip(names, results):
            if isinstance(res, Exception):
                logger.error(f"Health check failed for {name}: {res}")
                conn = self.connectors[name]
                self.health_cache[name] = SourceHealth(
                    name=conn.name,
                    domain=conn.domain,
                    status="UNAVAILABLE",
                    access_method=conn.access_method,
                    permission_status=conn.permission_status,
                    robots_policy=conn.robots_policy,
                    rate_limit=conn.rate_limit,
                    latency_ms=0,
                    error_count=1,
                    enabled=conn.enabled
                )
            else:
                self.health_cache[name] = res

        self.last_health_check = datetime.now(timezone.utc)
        return self.health_cache

    def get_registry_manifest(self) -> List[Dict[str, Any]]:
        """Returns public metadata and policies for the UI source health matrix."""
        manifest = []
        for key, conn in self.connectors.items():
            health = self.health_cache.get(key)
            manifest.append({
                "id": key,
                "name": conn.name,
                "domain": conn.domain,
                "access_method": conn.access_method,
                "permission_status": conn.permission_status,
                "robots_policy": conn.robots_policy,
                "rate_limit": conn.rate_limit,
                "status": health.status if health else ("LINK_OUT_ONLY" if conn.access_method == "LINK_OUT_ONLY" else "ONLINE"),
                "latency_ms": health.latency_ms if health else 0,
                "jobs_discovered": health.jobs_discovered if health else 0,
                "enabled": conn.enabled
            })
        return manifest

# Global registry singleton
source_registry = SourcePolicyRegistry()
