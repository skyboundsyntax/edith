"""Regression tests for keeping editorial results out of the job feed."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.firecrawl_service import (
    filter_job_listing_documents,
    is_job_listing_document,
)


def test_rejects_career_advice_article_that_mentions_jobs():
    article = {
        "url": "https://example.com/blog/how-to-write-a-job-description",
        "title": "How to write a great job description",
        "content": "Our career advice explains job requirements and hiring responsibilities.",
    }

    assert not is_job_listing_document(article)


def test_rejects_editorial_path_even_when_it_contains_jobs():
    article = {
        "url": "https://example.com/jobs/articles/hiring-trends",
        "title": "Hiring trends article",
        "content": "A news article about current job openings.",
    }

    assert not is_job_listing_document(article)


def test_accepts_direct_job_board_listing():
    listing = {
        "url": "https://www.linkedin.com/jobs/view/software-engineer-at-example-123456",
        "title": "Software Engineer at Example",
        "content": "Apply now. Job description, qualifications, and responsibilities.",
    }

    assert is_job_listing_document(listing)


def test_accepts_ats_career_listing_with_vacancy_signals():
    listing = {
        "url": "https://jobs.example.com/careers/platform-engineer",
        "title": "Platform Engineer | Example Careers",
        "content": "Apply now for this open position. Responsibilities and qualifications.",
    }

    assert is_job_listing_document(listing)


def test_filter_keeps_only_job_listings():
    documents = [
        {
            "url": "https://example.com/news/hiring-trends",
            "title": "Hiring trends report",
            "content": "A report about the job market.",
        },
        {
            "url": "https://jobs.example.com/jobs/data-analyst",
            "title": "Data Analyst",
            "content": "Apply now.",
        },
    ]

    assert filter_job_listing_documents(documents) == [documents[1]]
