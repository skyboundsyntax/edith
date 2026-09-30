"""
Intelligent Role & Domain Matching Engine for EDITH.
Ensures real-time job scrapers match genuine openings based on skills, roles, and technical domains.
Prevents false negatives caused by slight title variations across ATS platforms (e.g. SDE-2 vs Backend Developer).
"""
import re
from typing import Dict, List, Any, Optional

NON_TECH_ROLE_SIGNALS = [
    "account executive", "sales representative", "business development rep", "bdr",
    "recruiter", "talent acquisition", "sourcer", "hr generalist", "hr coordinator",
    "legal counsel", "paralegal", "facilities manager", "office coordinator",
    "receptionist", "executive assistant", "barista", "cashier", "nurse",
    "medical assistant", "physician", "dental", "phlebotomist", "warehouse associate",
    "delivery driver", "forklift operator", "call center", "telemarketer"
]

GENERIC_TECH_ROLES = [
    "software engineer", "developer", "programmer", "sde", "member of technical staff",
    "systems engineer", "platform engineer", "infrastructure engineer", "solutions architect",
    "technical lead", "tech lead", "engineering lead", "architect", "application engineer"
]

def is_matching_role(title: str, query_spec: Dict[str, Any], department: str = "", description: str = "") -> bool:
    """
    Evaluates whether a job posting matches the target role, skills, and technical domain of the search query.
    Handles semantic equivalence between engineering designations (e.g., SDE vs Software Engineer vs Developer).
    """
    if not title:
        return False

    title_lower = title.lower()
    dept_lower = (department or "").lower()
    desc_lower = (description or "").lower()[:500]

    # 1. Reject non-engineering roles unless user explicitly searched for them
    keywords = [k.lower() for k in (query_spec.get("keywords") or [])]
    roles = [r.lower() for r in (query_spec.get("roles") or [])]
    skills = [s.lower() for s in (query_spec.get("skills") or [])]

    is_explicit_non_tech = any(any(nt in item for nt in ["sales", "recruiter", "hr", "legal", "marketing"]) for item in (roles + keywords))
    if not is_explicit_non_tech:
        if any(re.search(r'\b' + re.escape(sig) + r'\b', title_lower) for sig in NON_TECH_ROLE_SIGNALS):
            return False

    # 2. If query has no constraints, any software/tech role matches
    if not keywords and not roles and not skills:
        return any(term in title_lower for term in ["engineer", "developer", "software", "data", "ai", "tech"]) or "engineering" in dept_lower

    # 3. Direct skill matches in title (e.g. Python, React, FastAPI, Go, Docker)
    for skill in skills:
        if len(skill) >= 2 and re.search(r'\b' + re.escape(skill) + r'\b', title_lower):
            return True

    # 4. Target domain matching:
    is_backend = any("backend" in r or "back-end" in r for r in roles) or any("backend" in k for k in keywords)
    is_frontend = any("frontend" in r or "front-end" in r for r in roles) or any("frontend" in k for k in keywords)
    is_fullstack = any("full" in r or "stack" in r for r in roles) or any("fullstack" in k or "full stack" in k for k in keywords)
    is_ai_ml = any(a in r for r in roles for a in ["ai", "ml", "data", "machine learning"]) or any(a in k for k in keywords for a in ["ai", "ml", "data", "deep learning"])
    is_devops = any(d in r for r in roles for d in ["devops", "cloud", "infra", "sre", "reliability"]) or any(d in k for k in keywords for d in ["devops", "cloud", "infra", "sre"])

    if is_backend:
        backend_keywords = ["backend", "back-end", "server", "api", "database", "infrastructure", "platform", "core", "systems", "distributed", "python", "golang", "java"]
        if any(re.search(r'\b' + re.escape(w) + r'\b', title_lower) for w in backend_keywords):
            return True
        if any(gen in title_lower for gen in GENERIC_TECH_ROLES):
            return True

    if is_frontend:
        frontend_keywords = ["frontend", "front-end", "ui", "ux", "web", "react", "vue", "angular", "javascript", "typescript", "client"]
        if any(re.search(r'\b' + re.escape(w) + r'\b', title_lower) for w in frontend_keywords):
            return True
        if any(gen in title_lower for gen in GENERIC_TECH_ROLES):
            return True

    if is_fullstack:
        fullstack_keywords = ["fullstack", "full stack", "full-stack", "web developer", "web engineer", "product engineer"]
        if any(re.search(r'\b' + re.escape(w) + r'\b', title_lower) for w in fullstack_keywords):
            return True
        if any(gen in title_lower for gen in GENERIC_TECH_ROLES):
            return True

    if is_ai_ml:
        ai_keywords = ["ai", "ml", "machine learning", "data scientist", "data science", "data engineer", "deep learning", "nlp", "llm", "computer vision", "generative ai", "research engineer"]
        if any(re.search(r'\b' + re.escape(w) + r'\b', title_lower) for w in ai_keywords):
            return True

    if is_devops:
        devops_keywords = ["devops", "cloud", "site reliability", "sre", "platform engineer", "kubernetes", "infra", "infrastructure", "security engineer"]
        if any(re.search(r'\b' + re.escape(w) + r'\b', title_lower) for w in devops_keywords):
            return True

    # 5. Word-by-word token fallback
    all_query_words = set()
    for item in (keywords + roles):
        for w in item.split():
            clean_w = re.sub(r'[^a-zA-Z0-9]', '', w).lower()
            if len(clean_w) > 2 and clean_w not in ["developer", "engineer", "jobs", "across", "india", "roles"]:
                all_query_words.add(clean_w)

    for qw in all_query_words:
        if re.search(r'\b' + re.escape(qw) + r'\b', title_lower):
            return True

    # 6. If title contains standard tech role and department is Engineering or Technology
    if any(term in title_lower for term in GENERIC_TECH_ROLES):
        if any(dept in dept_lower for dept in ["engineering", "product", "technology", "r&d", "software"]):
            return True

    return False
