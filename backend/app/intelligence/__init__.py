"""
Intelligence package for EDITH.
"""
from backend.app.intelligence.query_planner import (
    JobSearchSpecification,
    parse_job_query_to_spec
)
from backend.app.intelligence.match_scorer import (
    score_job_match,
    DEFAULT_WEIGHTS
)
from backend.app.intelligence.deduplicator import (
    deduplicate_jobs
)

__all__ = [
    "JobSearchSpecification",
    "parse_job_query_to_spec",
    "score_job_match",
    "DEFAULT_WEIGHTS",
    "deduplicate_jobs"
]
