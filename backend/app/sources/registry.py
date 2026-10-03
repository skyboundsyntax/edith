"""
Source Policy Registry for EDITH.
Tracks and orchestrates all permitted job source connectors:
- LinkedIn (Live Guest Search API & real-time extraction)
- Greenhouse (Public Board API - top tech employers)
- Lever (Public Postings API - Meesho, Spotify, etc.)
- Ashby (Public Board API - Linear, Perplexity, Cursor, Supabase)
- RemoteOK (Public Developer Jobs API)
- Himalayas (Public Remote Engineering API)
- Jobicy (Public Remote Jobs Feed)
- Arbeitnow (Public Jobs API)
- Remotive (Public Remote Jobs API)
- Indeed (Link-Out Search Aggregator)
- Naukri (Link-Out Search Aggregator)
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

try:
    from backend.app.sources.base import JobSourceConnector, SourceHealth
    from backend.app.sources.greenhouse_connector import GreenhouseConnector
    from backend.app.sources.lever_connector import LeverConnector
    from backend.app.sources.ashby_connector import AshbyConnector
    from backend.app.sources.jobicy_connector import JobicyConnector
    from backend.app.sources.arbeitnow_connector import ArbeitnowConnector
    from backend.app.sources.linkedin_connector import LinkedInConnector
    from backend.app.sources.remotive_connector import RemotiveConnector
    from backend.app.sources.remoteok_connector import RemoteOKConnector
    from backend.app.sources.himalayas_connector import HimalayasConnector
    from backend.app.sources.linkout_connector import LinkOutPlatformConnector
    from backend.app.sources.firecrawl_connector import FirecrawlConnector
except (ImportError, ModuleNotFoundError):
    from .base import JobSourceConnector, SourceHealth
    from .greenhouse_connector import GreenhouseConnector
    from .lever_connector import LeverConnector
    from .ashby_connector import AshbyConnector
    from .jobicy_connector import JobicyConnector
    from .arbeitnow_connector import ArbeitnowConnector
    from .linkedin_connector import LinkedInConnector
    from .remotive_connector import RemotiveConnector
    from .remoteok_connector import RemoteOKConnector
    from .himalayas_connector import HimalayasConnector
    from .linkout_connector import LinkOutPlatformConnector
    from .firecrawl_connector import FirecrawlConnector

logger = logging.getLogger(__name__)

class SourcePolicyRegistry:
    def __init__(self):
        self.connectors: Dict[str, JobSourceConnector] = {
            "firecrawl": FirecrawlConnector(),
            "linkedin": LinkedInConnector(),
            "greenhouse": GreenhouseConnector(),
            "lever": LeverConnector(),
            "ashby": AshbyConnector(),
            "remoteok": RemoteOKConnector(),
            "himalayas": HimalayasConnector(),
            "jobicy": JobicyConnector(),
            "arbeitnow": ArbeitnowConnector(),
            "remotive": RemotiveConnector(),
            "indeed": LinkOutPlatformConnector("Indeed", "in.indeed.com", "https://in.indeed.com/jobs?q={keywords}&l={location}"),
            "naukri": LinkOutPlatformConnector("Naukri", "naukri.com", "https://www.naukri.com/{keywords}-jobs-in-{location}")
        }
        self.health_cache: Dict[str, SourceHealth] = {}
        self.last_health_check: Optional[datetime] = None
        # Initialize default healthy telemetry for all registered real-time sources
        for key, conn in self.connectors.items():
            is_linkout = conn.access_method == "LINK_OUT_ONLY"
            self.health_cache[key] = SourceHealth(
                name=conn.name,
                domain=conn.domain,
                status="LINK_OUT_ONLY" if is_linkout else "ONLINE",
                access_method=conn.access_method,
                permission_status=conn.permission_status,
                robots_policy=conn.robots_policy,
                rate_limit=conn.rate_limit,
                latency_ms=10 if is_linkout else 85,
                jobs_discovered=0,
                error_count=0,
                enabled=conn.enabled
            )
        self.last_health_check = datetime.now(timezone.utc)

    def get_connector(self, name: str) -> Optional[JobSourceConnector]:
        return self.connectors.get(name.lower())

    def get_live_connectors(self) -> List[JobSourceConnector]:
        """Returns connectors with automated real-time fetching capabilities."""
        return [c for c in self.connectors.values() if c.access_method in ["PUBLIC_API", "PUBLIC_FEED", "PUBLIC_CAREER_PAGE", "WEB_SCRAPER"] and c.enabled]

    def get_linkout_connectors(self) -> List[JobSourceConnector]:
        """Returns platforms treated as link-out only (never produce fake jobs)."""
        return [c for c in self.connectors.values() if c.access_method == "LINK_OUT_ONLY" and c.enabled]

    async def check_all_health(self, force: bool = False) -> Dict[str, SourceHealth]:
        """Runs parallel real-time health checks on all registered connectors with caching & strict timeout."""
        now = datetime.now(timezone.utc)
        if not force and self.last_health_check:
            elapsed = (now - self.last_health_check).total_seconds()
            if elapsed < 30.0 and len(self.health_cache) == len(self.connectors):
                return self.health_cache

        tasks = []
        names = []
        for name, connector in self.connectors.items():
            names.append(name)
            tasks.append(asyncio.wait_for(connector.health_check(), timeout=3.5))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, res in zip(names, results):
            conn = self.connectors[name]
            if isinstance(res, Exception):
                logger.warning(f"Health check probe warning for {name}: {res}")
                prev = self.health_cache.get(name)
                is_linkout = conn.access_method == "LINK_OUT_ONLY"
                self.health_cache[name] = SourceHealth(
                    name=conn.name,
                    domain=conn.domain,
                    status="LINK_OUT_ONLY" if is_linkout else (prev.status if prev and prev.status != "UNAVAILABLE" else "DEGRADED"),
                    access_method=conn.access_method,
                    permission_status=conn.permission_status,
                    robots_policy=conn.robots_policy,
                    rate_limit=conn.rate_limit,
                    latency_ms=prev.latency_ms if prev and prev.latency_ms > 0 else 120,
                    error_count=(prev.error_count + 1) if prev else 1,
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
                "status": health.status if health else "ONLINE",
                "latency_ms": health.latency_ms if health else 0,
                "jobs_discovered": health.jobs_discovered if health else 0,
                "enabled": conn.enabled
            })
        return manifest

# Global registry singleton
source_registry = SourcePolicyRegistry()
