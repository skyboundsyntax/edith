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
    raw_prompt: Optional[str] = None


# Comprehensive domain taxonomy for skill and category inference
DOMAIN_ROLE_TAXONOMY = {
    # Gaming & 3D
    "game developer": {"role": "Game Developer", "skills": ["Game Development", "Unity", "Unreal Engine", "C#", "C++", "3D Animation"]},
    "game dev": {"role": "Game Developer", "skills": ["Game Development", "Unity", "Unreal Engine", "C#", "C++"]},
    "unity developer": {"role": "Unity Developer", "skills": ["Unity", "C#", "Game Development", "3D Modeling"]},
    "unreal developer": {"role": "Unreal Engine Developer", "skills": ["Unreal Engine", "C++", "Blueprints", "Game Physics"]},
    "game designer": {"role": "Game Designer", "skills": ["Game Design", "Level Design", "Mechanics", "Storyboarding"]},

    # Writing & Creative
    "copywriter": {"role": "Copywriter", "skills": ["Copywriting", "Content Writing", "SEO", "Creative Writing", "Editing"]},
    "copywriting": {"role": "Copywriter", "skills": ["Copywriting", "Content Writing", "SEO", "Creative Writing", "Advertising Copy"]},
    "content writer": {"role": "Content Writer", "skills": ["Content Writing", "SEO", "Blogging", "Research", "Copywriting"]},
    "technical writer": {"role": "Technical Writer", "skills": ["Technical Documentation", "API Docs", "Markdown", "Content Management"]},

    # Management & Operations
    "project manager": {"role": "Project Manager", "skills": ["Project Management", "Agile", "Scrum", "JIRA", "Stakeholder Management", "Budgeting"]},
    "program manager": {"role": "Program Manager", "skills": ["Program Management", "Roadmapping", "Cross-Functional Leadership", "Risk Management"]},
    "scrum master": {"role": "Scrum Master", "skills": ["Scrum", "Agile", "Sprint Planning", "JIRA", "Facilitation"]},
    "operations manager": {"role": "Operations Manager", "skills": ["Operations", "Process Improvement", "Team Leadership", "Budgeting"]},

    # Administration & Office
    "receptionist": {"role": "Receptionist", "skills": ["Front Desk", "Customer Service", "Office Administration", "Scheduling", "Communication", "MS Office"]},
    "front desk": {"role": "Front Desk Executive", "skills": ["Front Desk", "Customer Relations", "Phone Etiquette", "Visitor Management"]},
    "office assistant": {"role": "Office Assistant", "skills": ["Office Support", "Filing", "Data Entry", "MS Excel", "Scheduling"]},
    "data entry": {"role": "Data Entry Specialist", "skills": ["Data Entry", "MS Excel", "Typing", "Accuracy", "Back Office"]},
    "executive assistant": {"role": "Executive Assistant", "skills": ["Calendar Management", "Travel Coordination", "Correspondence", "Confidentiality"]},

    # Design
    "graphic designer": {"role": "Graphic Designer", "skills": ["Graphic Design", "Photoshop", "Illustrator", "Figma", "Branding"]},
    "ui designer": {"role": "UI Designer", "skills": ["UI Design", "Figma", "Design Systems", "Prototyping"]},
    "ux designer": {"role": "UX Designer", "skills": ["UX Research", "Wireframing", "Usability Testing", "User Journeys"]},
    "ui/ux designer": {"role": "UI/UX Designer", "skills": ["UI/UX Design", "Figma", "Wireframing", "User Research"]},

    # Finance & Accounts
    "accountant": {"role": "Accountant", "skills": ["Accounting", "Tally", "GST", "Financial Reporting", "Taxation", "Excel"]},
    "chartered accountant": {"role": "Chartered Accountant", "skills": ["Auditing", "Taxation", "Financial Analysis", "Compliance"]},
    "financial analyst": {"role": "Financial Analyst", "skills": ["Financial Modeling", "Valuation", "Forecasting", "Excel", "Data Analysis"]},

    # Sales & Marketing
    "sales executive": {"role": "Sales Executive", "skills": ["B2B Sales", "Lead Generation", "Negotiation", "CRM", "Cold Calling"]},
    "business development": {"role": "Business Development Executive", "skills": ["Business Development", "Client Acquisition", "Partnerships", "Sales Strategy"]},
    "digital marketer": {"role": "Digital Marketer", "skills": ["Digital Marketing", "SEO", "Google Ads", "Social Media Marketing", "Meta Ads"]},
    "seo specialist": {"role": "SEO Specialist", "skills": ["Search Engine Optimization", "Keyword Research", "Google Analytics", "On-Page SEO"]},

    # Engineering & Tech
    "software engineer": {"role": "Software Engineer", "skills": ["Software Engineering", "Problem Solving", "System Architecture", "Git"]},
    "software developer": {"role": "Software Developer", "skills": ["Software Development", "Programming", "Debugging", "Version Control"]},
    "frontend developer": {"role": "Frontend Developer", "skills": ["React", "JavaScript", "HTML", "CSS", "TypeScript"]},
    "backend developer": {"role": "Backend Developer", "skills": ["Python", "FastAPI", "Node.js", "APIs", "SQL", "Databases"]},
    "full stack developer": {"role": "Full Stack Developer", "skills": ["React", "Node.js", "Python", "SQL", "APIs", "JavaScript"]},
    "fullstack": {"role": "Full Stack Developer", "skills": ["React", "Python", "JavaScript", "SQL", "Full Stack"]},
    "data scientist": {"role": "Data Scientist", "skills": ["Python", "Machine Learning", "Pandas", "Statistics", "SQL"]},
    "data engineer": {"role": "Data Engineer", "skills": ["ETL", "SQL", "Python", "Apache Spark", "Data Pipelines"]},
    "data analyst": {"role": "Data Analyst", "skills": ["SQL", "Excel", "Tableau", "Power BI", "Python", "Data Visualization"]},
    "devops engineer": {"role": "DevOps Engineer", "skills": ["Docker", "Kubernetes", "CI/CD", "AWS", "Linux", "Terraform"]},
    "ai engineer": {"role": "AI Engineer", "skills": ["Python", "Deep Learning", "LLMs", "PyTorch", "Generative AI"]},
    "ml engineer": {"role": "ML Engineer", "skills": ["Machine Learning", "Python", "TensorFlow", "Scikit-Learn", "Model Training"]},
    "qa engineer": {"role": "QA Engineer", "skills": ["Manual Testing", "Automation", "Selenium", "Test Planning", "Bug Tracking"]},

    # Customer Service & Hospitality
    "customer support": {"role": "Customer Support Representative", "skills": ["Customer Service", "Ticketing", "Zendesk", "Communication", "Problem Resolution"]},
    "customer service": {"role": "Customer Service Representative", "skills": ["Customer Satisfaction", "Active Listening", "Conflict Resolution", "CRM"]},
    "chef": {"role": "Chef", "skills": ["Culinary Arts", "Kitchen Operations", "Food Safety", "Menu Planning"]},
    "teacher": {"role": "Teacher", "skills": ["Teaching", "Classroom Management", "Curriculum Development", "Communication"]}
}

ALL_INDIAN_STATES = {
    "orissa": "Orissa", "odisha": "Odisha", "maharashtra": "Maharashtra", "karnataka": "Karnataka",
    "tamil nadu": "Tamil Nadu", "telangana": "Telangana", "andhra pradesh": "Andhra Pradesh",
    "delhi": "Delhi NCR", "uttar pradesh": "Uttar Pradesh", "west bengal": "West Bengal",
    "kerala": "Kerala", "gujarat": "Gujarat", "rajasthan": "Rajasthan", "punjab": "Punjab",
    "haryana": "Haryana", "madhya pradesh": "Madhya Pradesh", "bihar": "Bihar", "goa": "Goa",
    "assam": "Assam", "jharkhand": "Jharkhand", "chhattisgarh": "Chhattisgarh", "uttarakhand": "Uttarakhand",
    "himachal pradesh": "Himachal Pradesh", "jammu": "Jammu & Kashmir", "kashmir": "Jammu & Kashmir"
}

ALL_MAJOR_CITIES = {
    "pune": "Pune", "bangalore": "Bangalore", "bengaluru": "Bengaluru", "mumbai": "Mumbai",
    "hyderabad": "Hyderabad", "chennai": "Chennai", "delhi": "Delhi", "noida": "Noida",
    "gurgaon": "Gurgaon", "gurugram": "Gurugram", "kolkata": "Kolkata", "ahmedabad": "Ahmedabad",
    "bhubaneswar": "Bhubaneswar", "cuttack": "Cuttack", "jaipur": "Jaipur", "chandigarh": "Chandigarh",
    "indore": "Indore", "kochi": "Kochi", "cochin": "Kochi", "coimbatore": "Coimbatore",
    "nagpur": "Nagpur", "lucknow": "Lucknow", "patna": "Patna", "bhopal": "Bhopal",
    "surat": "Surat", "vadodara": "Vadodara", "visakhapatnam": "Visakhapatnam", "vizag": "Visakhapatnam",
    "thiruvananthapuram": "Thiruvananthapuram", "trivandrum": "Thiruvananthapuram", "ranchi": "Ranchi",
    "guwahati": "Guwahati", "mysore": "Mysore", "mysuru": "Mysore", "dehradun": "Dehradun"
}


def parse_job_query_to_spec(natural_language_prompt: str) -> JobSearchSpecification:
    """
    Dynamically translates ANY user job prompt into a structured JobSearchSpecification.
    Supports tech, non-tech, creative, corporate, gig, and localized requests across any role or location.
    Strict rule: Never invent requirements. Search for what the user genuinely asked.
    """
    prompt = natural_language_prompt.strip()
    prompt_lower = prompt.lower()

    # 1. Modality & Remote Detection
    remote_pref = False
    if any(k in prompt_lower for k in ["online", "remote", "wfh", "work from home", "anywhere", "telecommute", "virtual", "freelance"]):
        remote_pref = True

    # 2. Location Extraction
    detected_locations = []

    # Check for "in <Location>", "at <Location>", "near <Location>", "for <Location>"
    loc_clause_match = re.search(r'\b(?:in|at|near|around|for)\s+([a-zA-Z\s]{2,30})\b', prompt_lower)
    if loc_clause_match:
        cand_loc = loc_clause_match.group(1).strip()
        # Clean trailing stop terms
        cand_loc = re.sub(r'\b(online|remote|jobs?|openings?|roles?|vacanc\w*|for|freshers?|experienced?)\b', '', cand_loc).strip()
        if cand_loc:
            # Check states
            if cand_loc in ALL_INDIAN_STATES:
                canonical_state = ALL_INDIAN_STATES[cand_loc]
                detected_locations.append(canonical_state)
                if cand_loc in ["orissa", "odisha"]:
                    detected_locations.extend(["Orissa", "Odisha"])
            # Check cities
            elif cand_loc in ALL_MAJOR_CITIES:
                detected_locations.append(ALL_MAJOR_CITIES[cand_loc])
            else:
                detected_locations.append(cand_loc.title())

    # Fallback to direct location keyword matches
    for state_alias, state_canonical in ALL_INDIAN_STATES.items():
        if re.search(r'\b' + re.escape(state_alias) + r'\b', prompt_lower):
            if state_canonical not in detected_locations:
                detected_locations.append(state_canonical)
            if state_alias in ["orissa", "odisha"]:
                for alt in ["Orissa", "Odisha"]:
                    if alt not in detected_locations:
                        detected_locations.append(alt)

    for city_alias, city_canonical in ALL_MAJOR_CITIES.items():
        if re.search(r'\b' + re.escape(city_alias) + r'\b', prompt_lower):
            if city_canonical not in detected_locations:
                detected_locations.append(city_canonical)

    if remote_pref and "Remote" not in detected_locations:
        detected_locations.append("Remote")

    detected_locations = list(dict.fromkeys(detected_locations))
    # If completely unconstrained, default to India or Remote
    if not detected_locations:
        detected_locations.append("India" if not remote_pref else "Remote")

    # 3. Salary & Compensation Extraction
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None

    # Check daily rates: "15k per day", "15000/day", "15k/day", "5000 daily"
    daily_match = re.search(r'(?:₹|rs\.?|inr|\$)?\s*(\d+(?:\.\d+)?)\s*(k|thousand)?\s*(?:per\s*day|\/day|daily|a\s*day)', prompt_lower)
    if daily_match:
        val = float(daily_match.group(1))
        if daily_match.group(2) or val < 100:
            val *= 1000.0
        # Convert daily to monthly equivalent (~25 working days)
        salary_min = val * 25.0
        salary_max = val * 30.0

    # Check monthly rates: "50k per month", "40,000/month", "50k/mo"
    elif re.search(r'(?:₹|rs\.?|inr|\$)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand)?\s*(?:per\s*month|\/month|monthly|\/mo|a\s*month)', prompt_lower):
        m_match = re.search(r'(?:₹|rs\.?|inr|\$)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(k|thousand)?\s*(?:per\s*month|\/month|monthly|\/mo|a\s*month)', prompt_lower)
        val = float(m_match.group(1).replace(",", ""))
        if m_match.group(2) or val < 1000:
            val *= 1000.0
        salary_min = val * 12.0

    # Check LPA ranges: "30-40 lpa", "30lpa-40lpa", "6 LPA"
    else:
        range_match = re.search(
            r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)?\s*(?:-|to)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)',
            prompt_lower
        )
        if range_match:
            salary_min = float(range_match.group(1)) * 100000.0
            salary_max = float(range_match.group(2)) * 100000.0
        else:
            single_match = re.search(
                r'(?:minimum|min|at least|starting)?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lpa|lac|lakh)',
                prompt_lower
            )
            if single_match:
                salary_min = float(single_match.group(1)) * 100000.0

    # 4. Experience Level
    exp_min: Optional[float] = None
    exp_max: Optional[float] = None
    exp_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?)', prompt_lower)
    if exp_match:
        exp_min = float(exp_match.group(1))
        exp_max = float(exp_match.group(2))
    elif any(k in prompt_lower for k in ["fresher", "freshers", "intern", "internship", "entry level", "student", "beginner"]):
        exp_min = 0.0
        exp_max = 1.0

    # 5. Employment Types
    employment_types = []
    if "intern" in prompt_lower or "internship" in prompt_lower:
        employment_types.append("Internship")
    if "freelance" in prompt_lower or "gig" in prompt_lower or "contract" in prompt_lower or "per day" in prompt_lower:
        employment_types.append("Freelance")
    if "part time" in prompt_lower or "part-time" in prompt_lower:
        employment_types.append("Part-time")
    if not employment_types:
        employment_types.append("Full-time")

    # 6. Dynamic Target Role & Skill Extraction
    detected_roles = []
    detected_skills = []

    # A. Check against comprehensive taxonomy
    for key, data in DOMAIN_ROLE_TAXONOMY.items():
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, prompt_lower):
            if data["role"] not in detected_roles:
                detected_roles.append(data["role"])
            for s in data["skills"]:
                if s not in detected_skills:
                    detected_skills.append(s)

    # B. Heuristic extraction if no dictionary role matched
    if not detected_roles:
        # Strip location, salary, experience, modality, and noise to isolate the true target role
        core_query = prompt_lower
        # Remove location clause
        if loc_clause_match:
            core_query = core_query.replace(loc_clause_match.group(0), " ")
        for s_alias in list(ALL_INDIAN_STATES.keys()) + list(ALL_MAJOR_CITIES.keys()):
            core_query = re.sub(r'\b' + re.escape(s_alias) + r'\b', " ", core_query)
        # Remove salary
        core_query = re.sub(r'(?:₹|rs\.?|inr|\$)?\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:k|thousand)?\s*(?:per\s*(?:day|month|year|hr)|\/day|\/month|lpa|lac|lakh|daily|monthly)', " ", core_query)
        # Remove experience
        core_query = re.sub(r'\d+\s*(?:-|to)\s*\d+\s*(?:years?|yrs?)|(?:for\s*)?freshers?|entry\s*level|interns?|internships?', " ", core_query)
        # Remove modality & generic filler
        stop_filler = [
            "looking for", "find me", "search for", "search", "i want", "need a", "want a", "urgently",
            "openings for", "opening for", "vacancies for", "vacancy for", "jobs for", "job for",
            "jobs in", "job in", "openings in", "opening in", "vacancies in", "vacancy in",
            "jobs", "job", "openings", "opening", "vacancies", "vacancy", "roles", "role", "positions", "position",
            "online", "remote", "offline", "hybrid", "wfh", "work from home", "in", "at", "for", "near", "with", "and", "or", "a", "an", "the"
        ]
        tokens = [w.strip() for w in core_query.split() if w.strip()]
        cleaned_tokens = [t for t in tokens if t not in stop_filler and len(t) > 1]
        isolated_role = " ".join(cleaned_tokens).strip()

        if isolated_role:
            canonical_role = isolated_role.title()
            detected_roles.append(canonical_role)
            detected_skills.append(canonical_role)
        else:
            detected_roles.append("Job Opening")

    # 7. Build Search Keywords
    # Keywords MUST include the target role, skills, and query terms
    search_keywords = list(dict.fromkeys(
        [r.lower() for r in detected_roles] +
        [s.lower() for s in detected_skills[:4]] +
        [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', prompt_lower) if w not in ["find", "search", "want", "jobs", "job", "with", "from", "the", "and"]]
    ))

    # Excluded keywords
    excluded = []
    if exp_max is not None and exp_max <= 2:
        excluded.extend(["Senior", "Lead", "Staff", "Principal", "5+ years", "8+ years"])

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
        industries=[],
        preferred_sources=[],
        excluded_keywords=excluded,
        freshness_hours=72,
        raw_prompt=prompt
    )

