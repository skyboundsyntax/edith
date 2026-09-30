"""
AI Query Planner for EDITH.
Converts free-form natural language job queries into structured search specifications.
Strict rule: Never invent requirements. Missing values MUST remain null.
"""
import re
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from backend.app.locations.india_locations import INDIAN_TECH_HUBS

class JobSearchSpecification(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    employment_types: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    remote: bool = False
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    companies: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    preferred_sources: List[str] = Field(default_factory=list)
    excluded_keywords: List[str] = Field(default_factory=list)
    freshness_hours: Optional[int] = 72


KNOWN_TECH_SKILLS = [
    "python", "react", "javascript", "typescript", "fastapi", "django", "flask",
    "machine learning", "ml", "ai", "artificial intelligence", "deep learning", "pytorch", "tensorflow",
    "sql", "postgresql", "mysql", "mongodb", "docker", "kubernetes", "aws", "gcp", "azure",
    "node.js", "nodejs", "c++", "java", "golang", "go", "rust", "html", "css", "vue", "next.js",
    "data science", "nlp", "llm", "generative ai", "computer vision", "git", "rest api"
]

ROLE_KEYWORDS = {
    "intern": "Intern",
    "internship": "Internship",
    "junior": "Junior Engineer",
    "entry level": "Entry-Level Engineer",
    "fresher": "Fresher",
    "frontend": "Frontend Developer",
    "backend": "Backend Developer",
    "full stack": "Full Stack Developer",
    "fullstack": "Full Stack Developer",
    "software engineer": "Software Engineer",
    "sde": "Software Development Engineer",
    "ai engineer": "AI Engineer",
    "ml engineer": "ML Engineer",
    "data scientist": "Data Scientist",
    "devops": "DevOps Engineer"
}


def parse_job_query_to_spec(natural_language_prompt: str) -> JobSearchSpecification:
    """
    Parses a natural-language job request into a deterministic JobSearchSpecification.
    Adheres strictly to 'Missing values must remain null. Never invent requirements.'
    """
    prompt = natural_language_prompt.strip()
    prompt_lower = prompt.lower()

    # 1. Detect target skills
    detected_skills = []
    for skill in KNOWN_TECH_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, prompt_lower):
            detected_skills.append(skill.title() if len(skill) > 3 else skill.upper())

    # 2. Detect target roles
    detected_roles = []
    for role_trigger, canonical_role in ROLE_KEYWORDS.items():
        pattern = r'\b' + re.escape(role_trigger) + r'\b'
        if re.search(pattern, prompt_lower):
            if canonical_role not in detected_roles:
                detected_roles.append(canonical_role)

    # 3. Detect experience constraints
    exp_min: Optional[float] = None
    exp_max: Optional[float] = None

    # Matches patterns like "0-2 years", "0 to 1 yr", "0-1 yrs exp", "fresher"
    exp_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?)', prompt_lower)
    if exp_match:
        exp_min = float(exp_match.group(1))
        exp_max = float(exp_match.group(2))
    elif "fresher" in prompt_lower or "2nd year" in prompt_lower or "second year" in prompt_lower or "intern" in prompt_lower:
        exp_min = 0.0
        exp_max = 1.0
    else:
        # Check for single constraint like "less than 2 years", "max 1 year"
        max_match = re.search(r'(?:less than|not more than|max|up to|maximum)\s*(\d+)\s*(?:years?|yrs?)', prompt_lower)
        if max_match:
            exp_min = 0.0
            exp_max = float(max_match.group(1))

    # 4. Employment types
    employment_types = []
    if "intern" in prompt_lower or "internship" in prompt_lower:
        employment_types.append("Internship")
    if "full time" in prompt_lower or "full-time" in prompt_lower or "entry level" in prompt_lower:
        employment_types.append("Full-time")
    if not employment_types:
        employment_types.append("Full-time")

    # 5. Locations and Remote
    detected_locations = []
    remote_pref = False

    if any(k in prompt_lower for k in ["remote", "wfh", "work from home", "anywhere"]):
        remote_pref = True

    for hub_key, hub_data in INDIAN_TECH_HUBS.items():
        for alias in hub_data["aliases"]:
            if re.search(r'\b' + re.escape(alias) + r'\b', prompt_lower):
                if hub_data["canonical"] not in detected_locations:
                    detected_locations.append(hub_data["canonical"])
                break

    # India is the default geographic scope if no specific city is requested
    if not detected_locations:
        detected_locations.append("India")
    elif "India" not in detected_locations and any(k in prompt_lower for k in ["india", "pan india", "across india"]):
        detected_locations.append("India")

    # 6. Salary Bracket / Range (e.g. "30lpa-40lpa", "30-40 LPA", "₹30-40 LPA", "minimum 6 LPA")
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None

    # Check for range: e.g. "30lpa-40lpa", "30-40 lpa", "30 to 40 lpa", "₹30 - 40 LPA"
    range_match = re.search(
        r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)?\s*(?:-|to)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)',
        prompt_lower
    )
    if range_match:
        salary_min = float(range_match.group(1)) * 100000.0
        salary_max = float(range_match.group(2)) * 100000.0
    else:
        # Check for minimum or single LPA: e.g. "30 LPA", "minimum 6 LPA", "30lpa"
        single_match = re.search(
            r'(?:minimum|min|at least|starting)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)',
            prompt_lower
        )
        if single_match:
            salary_min = float(single_match.group(1)) * 100000.0

    # 7. Excluded keywords (e.g. "don't want jobs requiring more than 1 year", "no senior")
    excluded = []
    if exp_max is not None and exp_max <= 2:
        excluded.extend(["Senior", "Lead", "Staff", "Principal", "5+ years", "8+ years"])

    # 8. Industries and Company Preferences
    industries = []
    if "startup" in prompt_lower:
        industries.append("Startups")
    if "product" in prompt_lower:
        industries.append("Product Companies")

    # 9. Freshness hours (default 72 hours if not specified)
    freshness = 72
    if "last 24 hours" in prompt_lower or "today" in prompt_lower or "last 1 day" in prompt_lower:
        freshness = 24
    elif "last 7 days" in prompt_lower or "past week" in prompt_lower:
        freshness = 168
    elif "last 3 days" in prompt_lower:
        freshness = 72

    # Assemble keywords for search connectors
    search_keywords = list(dict.fromkeys(
        [s.lower() for s in detected_skills] +
        [r.lower() for r in detected_roles]
    ))

    return JobSearchSpecification(
        keywords=search_keywords,
        roles=detected_roles,
        skills=detected_skills,
        experience_min=exp_min,
        experience_max=exp_max,
        employment_types=employment_types,
        locations=detected_locations,
        remote=remote_pref,
        salary_min=salary_min,
        salary_max=salary_max,
        companies=[],
        industries=industries,
        preferred_sources=[],
        excluded_keywords=excluded,
        freshness_hours=freshness
    )
