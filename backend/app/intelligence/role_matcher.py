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
    Evaluates whether a job posting matches the user's requested role, skills, and domain.
    Works universally across ANY profession (tech, creative, corporate, hospitality, admin, gig, etc.).
    """
    if not title:
        return False

    title_lower = title.lower()
    dept_lower = (department or "").lower()
    desc_lower = (description or "").lower()[:600]

    keywords = [k.lower() for k in (query_spec.get("keywords") or [])]
    roles = [r.lower() for r in (query_spec.get("roles") or [])]
    skills = [s.lower() for s in (query_spec.get("skills") or [])]

    # 1. Direct Target Role Match (Highest priority)
    for r in roles:
        r_clean = re.sub(r'[^a-zA-Z0-9\s]', '', r).strip()
        # Direct phrase match
        if r_clean and r_clean in title_lower:
            return True
        # Match individual significant tokens (e.g. 'receptionist', 'copywriter', 'manager', 'game')
        r_tokens = [tok for tok in r_clean.split() if len(tok) >= 3 and tok not in ["job", "jobs", "opening", "openings", "role", "roles", "for", "the"]]
        if r_tokens and any(re.search(r'\b' + re.escape(tok) + r'\b', title_lower) for tok in r_tokens):
            return True

    # 2. Direct Keyword Match in Title
    for kw in keywords:
        kw_clean = re.sub(r'[^a-zA-Z0-9\s]', '', kw).strip()
        if len(kw_clean) >= 3:
            if re.search(r'\b' + re.escape(kw_clean) + r'\b', title_lower):
                return True

    # 3. Direct Skill Match in Title or Description
    for skill in skills:
        if len(skill) >= 2 and re.search(r'\b' + re.escape(skill) + r'\b', title_lower):
            return True

    # 4. Filter out non-tech signals ONLY IF the user explicitly searched for software/coding
    is_user_seeking_software = any(any(sw in item for sw in ["software", "sde", "developer", "backend", "frontend", "fullstack", "devops", "cloud engineer", "ai engineer", "ml engineer"]) for item in (roles + keywords))
    if is_user_seeking_software:
        # User explicitly wants software/engineering; drop non-tech signals
        if any(re.search(r'\b' + re.escape(sig) + r'\b', title_lower) for sig in NON_TECH_ROLE_SIGNALS):
            return False

    # 5. Engineering domain fallbacks if user asked for engineering
    if is_user_seeking_software:
        is_backend = any("backend" in r or "back-end" in r for r in roles) or any("backend" in k for k in keywords)
        is_frontend = any("frontend" in r or "front-end" in r for r in roles) or any("frontend" in k for k in keywords)
        is_fullstack = any("full" in r or "stack" in r for r in roles) or any("fullstack" in k or "full stack" in k for k in keywords)
        is_ai_ml = any(a in r for r in roles for a in ["ai", "ml", "data", "machine learning"]) or any(a in k for k in keywords for a in ["ai", "ml", "data", "deep learning"])
        is_devops = any(d in r for r in roles for d in ["devops", "cloud", "infra", "sre", "reliability"]) or any(d in k for k in keywords for d in ["devops", "cloud", "infra", "sre"])

        if is_backend and any(w in title_lower for w in ["backend", "back-end", "server", "api", "database", "platform", "core", "systems", "python", "golang", "java"]):
            return True
        if is_frontend and any(w in title_lower for w in ["frontend", "front-end", "ui", "ux", "web", "react", "vue", "angular", "javascript", "typescript", "client"]):
            return True
        if is_fullstack and any(w in title_lower for w in ["fullstack", "full stack", "full-stack", "web developer", "web engineer"]):
            return True
        if is_ai_ml and any(w in title_lower for w in ["ai", "ml", "machine learning", "data scientist", "data science", "deep learning", "nlp", "llm"]):
            return True
        if is_devops and any(w in title_lower for w in ["devops", "cloud", "sre", "platform engineer", "kubernetes", "infra"]):
            return True

        if any(gen in title_lower for gen in GENERIC_TECH_ROLES):
            return True

    # 6. Fallback: Word-by-word query token match in title or description
    all_query_words = set()
    for item in (keywords + roles + skills):
        for w in item.split():
            clean_w = re.sub(r'[^a-zA-Z0-9]', '', w).lower()
            if len(clean_w) >= 3 and clean_w not in ["jobs", "job", "opening", "openings", "across", "india", "roles", "role"]:
                all_query_words.add(clean_w)

    for qw in all_query_words:
        if re.search(r'\b' + re.escape(qw) + r'\b', title_lower):
            return True

    # 7. Unconstrained query: match any real job opening
    if not keywords and not roles and not skills:
        return True

    return False
