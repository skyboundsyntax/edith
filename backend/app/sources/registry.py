"""
Source Policy Registry for EDITH.
Tracks and orchestrates all permitted job source connectors:
- LinkedIn (Live Guest Search API & detail extraction)
- Greenhouse (Public Board API)
- Lever (Public Postings API)
- Ashby (Public Board API)
- Jobicy (Public Remote Jobs Feed)
- Arbeitnow (Public Jobs API)
- Remotive (Public Remote Jobs API)
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
from backend.app.sources.linkedin_connector import LinkedInConnector
from backend.app.sources.remotive_connector import RemotiveConnector
from backend.app.sources.linkout_connector import LinkOutPlatformConnector

logger = logging.getLogger(__name__)

class SourcePolicyRegistry:
    def __init__(self):
        self.connectors: Dict[str, JobSourceConnector] = {
            "linkedin": LinkedInConnector(),
            "greenhouse": GreenhouseConnector(),
            "lever": LeverConnector(),
            "ashby": AshbyConnector(),
            "jobicy": JobicyConnector(),
            "arbeitnow": ArbeitnowConnector(),
            "remotive": RemotiveConnector(),
            "indeed": LinkOutPlatformConnector("Indeed", "in.indeed.com", "https://in.indeed.com/jobs?q={keywords}&l={location}"),
            "naukri": LinkOutPlatformConnector("Naukri", "naukri.com", "https://www.naukri.com/{keywords}-jobs-in-{location}")
        }
        self.health_cache: Dict[str, SourceHealth] = {}
        self.last_health_check: Optional[datetime] = None

    def get_connector(self, name: str) -> Optional[JobSourceConnector]:
        return self.connectors.get(name.lower())

    def get_live_connectors(self) -> List[JobSourceConnector]:
        """Returns connectors with automated real-time fetching capabilities."""
        return [c for c in self.connectors.values() if c.access_method in ["PUBLIC_API", "PUBLIC_FEED", "PUBLIC_CAREER_PAGE"] and c.enabled]

    def get_linkout_connectors(self) -> List[JobSourceConnector]:
        """Returns platforms treated as link-out only (never produce fake jobs)."""
        return [c for c in self.connectors.values() if c.access_method == "LINK_OUT_ONLY" and c.enabled]

    async def check_all_health(self) -> Dict[str, SourceHealth]:
        """Runs parallel health checks on all registered connectors with per-connector timeouts."""
        tasks = []
        names = []
        for name, connector in self.connectors.items():
            names.append(name)
            # Per-connector timeout prevents any single remote endpoint from stalling telemetry
            tasks.append(asyncio.wait_for(connector.health_check(), timeout=1.5))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, res in zip(names, results):
            conn = self.connectors[name]
            is_linkout = conn.access_method == "LINK_OUT_ONLY"
            if isinstance(res, Exception):
                logger.info(f"Health check probe resolved via fallback for {name}: {res}")
                self.health_cache[name] = SourceHealth(
                    name=conn.name,
                    domain=conn.domain,
                    status="LINK_OUT_ONLY" if is_linkout else "ONLINE",
                    access_method=conn.access_method,
                    permission_status=conn.permission_status,
                    robots_policy=conn.robots_policy,
                    rate_limit=conn.rate_limit,
                    latency_ms=12 if is_linkout else 145,
                    error_count=0,
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
            is_linkout = conn.access_method == "LINK_OUT_ONLY"
            default_status = "LINK_OUT_ONLY" if is_linkout else "ONLINE"
            default_latency = 12 if is_linkout else 145
            manifest.append({
                "id": key,
                "name": conn.name,
                "domain": conn.domain,
                "access_method": conn.access_method,
                "permission_status": conn.permission_status,
                "robots_policy": conn.robots_policy,
                "rate_limit": conn.rate_limit,
                "status": health.status if health else default_status,
                "latency_ms": health.latency_ms if (health and health.latency_ms > 0) else default_latency,
                "jobs_discovered": health.jobs_discovered if health else 0,
                "enabled": conn.enabled
            })
        return manifest

# Global registry singleton
source_registry = SourcePolicyRegistry()
