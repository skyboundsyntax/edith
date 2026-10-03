"""Regression coverage for job intent parsing and location-aware live results."""

import asyncio

from backend.app.api import sources
from backend.app.api.sources import (
    FirecrawlSearchRequest,
    _matches_job_search_preferences,
)
from backend.app.intelligence.query_planner import parse_job_query_to_spec
from backend.app.intelligence.role_matcher import is_matching_role


def test_game_developer_query_is_classified_as_a_job_search():
    spec = parse_job_query_to_spec("game dev jobs in Pune").model_dump()

    assert spec["roles"] == ["Game Developer"]
    assert spec["locations"] == ["Pune"]
    assert spec["intent_parsing"]["domain_type"] == "TALENT_JOBS"


def test_arbitrary_job_roles_are_extracted_and_matched():
    for query, expected_role in (
        ("copywriter jobs in Pune", "Copywriter"),
        ("receptionist jobs in Pune", "Receptionist"),
        ("barista jobs in Pune", "Barista"),
    ):
        spec = parse_job_query_to_spec(query).model_dump()
        assert expected_role in spec["roles"]
        assert spec["intent_parsing"]["domain_type"] == "TALENT_JOBS"
        assert is_matching_role(expected_role, spec)


def test_live_results_obey_requested_role_and_location():
    spec = parse_job_query_to_spec("game dev jobs in Pune").model_dump()

    assert _matches_job_search_preferences(
        {"title": "Unity Developer", "location": "Pune, Maharashtra, India"},
        spec,
    )
    assert not _matches_job_search_preferences(
        {"title": "Unity Developer", "location": "Remote"},
        spec,
    )
    assert not _matches_job_search_preferences(
        {"title": "Frontend Developer", "location": "Pune, Maharashtra, India"},
        spec,
    )
    assert not _matches_job_search_preferences(
        {"title": "Unity Developer", "location": "London, UK"},
        spec,
    )


def test_remote_preference_allows_remote_listings():
    spec = parse_job_query_to_spec("remote game dev jobs").model_dump()

    assert _matches_job_search_preferences(
        {"title": "Game Developer", "location": "Remote"},
        spec,
    )


def test_live_search_response_does_not_return_jobs_outside_requested_city(monkeypatch):
    async def fake_search(self, query, max_results):
        return [
            {
                "url": "https://jobs.example.com/pune-game-dev",
                "title": "Game Developer",
                "source": "LinkedIn Jobs",
                "metadata": {
                    "job_title": "Game Developer",
                    "company": "Pune Games",
                    "location": "Pune, Maharashtra, India",
                    "apply_link": "https://jobs.example.com/pune-game-dev",
                },
            },
            {
                "url": "https://jobs.example.com/remote-game-dev",
                "title": "Game Developer",
                "source": "LinkedIn Jobs",
                "metadata": {
                    "job_title": "Game Developer",
                    "company": "Remote Games",
                    "location": "Remote",
                    "apply_link": "https://jobs.example.com/remote-game-dev",
                },
            },
        ]

    monkeypatch.setattr(sources.SourceDiscovery, "search", fake_search)
    response = asyncio.run(
        sources.search_firecrawl(
            FirecrawlSearchRequest(query="game dev jobs in Pune")
        )
    )

    assert [job["company"] for job in response["jobs"]] == ["Pune Games"]
