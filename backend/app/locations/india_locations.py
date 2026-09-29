"""
India-First Location Normalization and Intelligence Module for EDITH.
Modular and extensible: allows adding international locations later.
"""
import re
from typing import Dict, Optional, Tuple, List

INDIAN_TECH_HUBS = {
    "bangalore": {
        "canonical": "Bangalore",
        "state": "Karnataka",
        "country": "India",
        "aliases": ["bengaluru", "bangalore", "blr", "whitefield", "electronic city", "koramangala", "bellandur", "indiranagar", "harlur", "marathahalli"]
    },
    "pune": {
        "canonical": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "aliases": ["pune", "hinjewadi", "magarpatta", "viman nagar", "baner", "wakad", "kharadi", "hadapsar", "kothrud", "aundh", "senapati bapat"]
    },
    "mumbai": {
        "canonical": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "aliases": ["mumbai", "bombay", "navi mumbai", "thane", "bkc", "andheri", "powai", "bandra", "goregaon"]
    },
    "hyderabad": {
        "canonical": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "aliases": ["hyderabad", "secunderabad", "hitech city", "gachibowli", "madhapur", "kondapur", "hyd", "financial district", "manikonda"]
    },
    "chennai": {
        "canonical": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "aliases": ["chennai", "madras", "omr", "t nagar", "guindy", "velachery", "sholinganallur", "siruseri"]
    },
    "delhi_ncr": {
        "canonical": "Delhi NCR",
        "state": "Delhi NCR",
        "country": "India",
        "aliases": ["delhi", "new delhi", "delhi ncr", "ncr", "connaught place", "south delhi", "nehru place"]
    },
    "gurgaon": {
        "canonical": "Gurgaon",
        "state": "Haryana",
        "country": "India",
        "aliases": ["gurgaon", "gurugram", "cyber city", "sohna road", "golf course road", "udyog vihar", "dlf phase"]
    },
    "noida": {
        "canonical": "Noida",
        "state": "Uttar Pradesh",
        "country": "India",
        "aliases": ["noida", "greater noida", "sector 62", "sector 18", "sector 125", "sector 63"]
    },
    "kolkata": {
        "canonical": "Kolkata",
        "state": "West Bengal",
        "country": "India",
        "aliases": ["kolkata", "calcutta", "salt lake", "new town", "sector v"]
    },
    "ahmedabad": {
        "canonical": "Ahmedabad",
        "state": "Gujarat",
        "country": "India",
        "aliases": ["ahmedabad", "gandhinagar", "gift city"]
    },
    "jaipur": {
        "canonical": "Jaipur",
        "state": "Rajasthan",
        "country": "India",
        "aliases": ["jaipur", "pink city", "sitapura", "malviya nagar"]
    },
    "kochi": {
        "canonical": "Kochi",
        "state": "Kerala",
        "country": "India",
        "aliases": ["kochi", "cochin", "kerala", "infopark", "kakkanad"]
    },
    "chandigarh": {
        "canonical": "Chandigarh",
        "state": "Punjab / Haryana",
        "country": "India",
        "aliases": ["chandigarh", "mohali", "panchkula"]
    },
    "indore": {
        "canonical": "Indore",
        "state": "Madhya Pradesh",
        "country": "India",
        "aliases": ["indore", "super corridor", "crystal it park"]
    },
    "coimbatore": {
        "canonical": "Coimbatore",
        "state": "Tamil Nadu",
        "country": "India",
        "aliases": ["coimbatore", "saravanampatti", "peelamedu"]
    }
}

REMOTE_KEYWORDS = [
    "remote", "work from home", "wfh", "anywhere", "telecommute", "distributed", "virtual", "homeoffice"
]

HYBRID_KEYWORDS = [
    "hybrid", "flexible", "partial remote", "2-3 days remote"
]

# Explicit foreign locations and restrictions
FOREIGN_REGIONS = {
    "United States": [
        "usa", "united states", "u.s.", "u.s.a", "us only", "usa only", "america", "san francisco",
        "new york", "seattle", "austin", "california", "los angeles", "boston", "chicago",
        "mountain view", "sunnyvale", "palo alto", "san jose", "denver", "atlanta", "dallas",
        "houston", "miami", "washington dc", "remote (usa)", "remote us", "us remote", "remote - us",
        "remote - usa", "remote, united states", "remote in usa", "mountain plains", "pacific/mountain",
        "north america", "northern america"
    ],
    "United Kingdom": [
        "uk", "united kingdom", "great britain", "england", "london", "manchester", "birmingham", "edinburgh", "scotland"
    ],
    "Canada": [
        "canada", "toronto", "vancouver", "montreal", "ottawa", "waterloo", "calgary", "remote (canada)"
    ],
    "Europe": [
        "europe", "emea", "eu", "germany", "deutschland", "berlin", "munich", "frankfurt", "hamburg",
        "france", "paris", "spain", "madrid", "barcelona", "netherlands", "amsterdam", "poland",
        "warsaw", "czechia", "czech republic", "slovakia", "prague", "bratislava", "sweden",
        "stockholm", "switzerland", "zurich", "geneva", "ireland", "dublin", "austria", "vienna",
        "italy", "rome", "milan", "portugal", "lisbon", "norway", "oslo", "finland", "helsinki",
        "denmark", "copenhagen", "belgium", "brussels"
    ],
    "Asia-Pacific (Non-India)": [
        "singapore", "thailand", "bangkok", "japan", "tokyo", "malaysia", "kuala lumpur",
        "indonesia", "jakarta", "vietnam", "philippines", "manila", "hong kong", "taiwan",
        "taipei", "china", "beijing", "shanghai", "korea", "seoul", "australia", "sydney",
        "melbourne", "new zealand", "auckland", "apj"
    ],
    "Latin America": [
        "latam", "latin america", "brazil", "sao paulo", "mexico", "mexico city", "argentina",
        "buenos aires", "colombia", "bogota", "peru", "lima", "chile", "santiago"
    ]
}

WORLDWIDE_KEYWORDS = [
    "worldwide", "anywhere", "global", "work from anywhere", "remote - worldwide",
    "remote worldwide", "worldwide (remote)", "all locations", "remote, global"
]

# Patterns for crowdwork, microtasks, online survey, online tutors, language training gigs
ONLINE_GIG_TITLE_PATTERNS = [
    r"\blanguage trainer\b", r"\bcontent reviewer\b", r"\bonline tutor\b", r"\bonline teacher\b",
    r"\bsurvey\b", r"\bmicrotask\b", r"\brating task\b", r"\bonline evaluator\b",
    r"\btranscriptionist\b", r"\bdata entry\b", r"\bkundenservice\b", r"\bfinanzvertrieb\b",
    r"\bcall center\b", r"\btelemarketer\b", r"\bmystery shopper\b", r"\brater\b",
    r"\bclickworker\b", r"\bannotator\b", r"\bsearch evaluator\b"
]

ONLINE_GIG_DESC_PATTERNS = [
    r"\bper completed task\b", r"\bfreelance project.*rate of pay\b",
    r"\bevaluating online content\b", r"\brating program\b", r"\bmicrotask\b",
    r"\bmust have resided in the united states\b", r"\bdeliver language classes\b"
]


def is_online_gig(title: str, description: str = "") -> bool:
    """
    Detects low-quality microtasks, crowdwork, content rating, online language training,
    or non-engineering online tasks that should not masquerade as tech/developer jobs.
    """
    t_lower = (title or "").lower()
    d_lower = (description or "").lower()

    for pat in ONLINE_GIG_TITLE_PATTERNS:
        if re.search(pat, t_lower):
            return True

    for pat in ONLINE_GIG_DESC_PATTERNS:
        if re.search(pat, d_lower):
            return True

    return False


def normalize_location(raw_location: str) -> Dict[str, Any]:
    """
    Normalizes any raw location string into canonical city, state, country, remote type,
    and flags for India vs Foreign vs Worldwide compatibility.
    """
    if not raw_location or not str(raw_location).strip():
        return {
            "canonical_location": "Remote / Unspecified",
            "city": None,
            "state": None,
            "country": "India",
            "remote_type": "remote",
            "is_india": True,
            "is_worldwide": False,
            "is_foreign": False
        }

    raw_str = str(raw_location).strip()
    raw_lower = raw_str.lower()

    # Detect remote/hybrid
    remote_type = "on-site"
    if any(k in raw_lower for k in REMOTE_KEYWORDS):
        remote_type = "remote"
    elif any(k in raw_lower for k in HYBRID_KEYWORDS):
        remote_type = "hybrid"

    # Check for Indian tech hub
    matched_hub = None
    for hub_key, hub_data in INDIAN_TECH_HUBS.items():
        for alias in hub_data["aliases"]:
            if re.search(r'\b' + re.escape(alias) + r'\b', raw_lower):
                matched_hub = hub_data
                break
        if matched_hub:
            break

    if matched_hub:
        city = matched_hub["canonical"]
        state = matched_hub["state"]
        country = matched_hub["country"]
        if remote_type == "remote":
            canonical = f"{city} (Remote / Hybrid)"
        else:
            canonical = f"{city}, {state}, {country}"
        return {
            "canonical_location": canonical,
            "city": city,
            "state": state,
            "country": country,
            "remote_type": remote_type,
            "work_modality": "Online" if remote_type == "remote" else "Offline",
            "is_india": True,
            "is_worldwide": False,
            "is_foreign": False
        }

    # Check for general India match
    if re.search(r'\b(india|pan india)\b', raw_lower) or raw_lower in ["in", "/in", "india"]:
        return {
            "canonical_location": "India (Remote)" if remote_type == "remote" else "India",
            "city": None,
            "state": None,
            "country": "India",
            "remote_type": remote_type,
            "work_modality": "Online" if remote_type == "remote" else "Offline",
            "is_india": True,
            "is_worldwide": False,
            "is_foreign": False
        }

    # Check for Worldwide / Global / Anywhere
    if any(re.search(r'\b' + re.escape(w) + r'\b', raw_lower) for w in WORLDWIDE_KEYWORDS):
        # But verify it doesn't also restrict to a foreign region like 'Remote (Europe, USA)'
        has_foreign = False
        for reg_name, reg_aliases in FOREIGN_REGIONS.items():
            if any(re.search(r'\b' + re.escape(a) + r'\b', raw_lower) for a in reg_aliases):
                has_foreign = True
                break
        if not has_foreign:
            return {
                "canonical_location": "Worldwide (Remote)",
                "city": "Worldwide",
                "state": None,
                "country": "Worldwide",
                "remote_type": "remote",
                "work_modality": "Online",
                "is_india": False,
                "is_worldwide": True,
                "is_foreign": False
            }

    # Check for Foreign Regions (USA, UK, Europe, etc.)
    for reg_name, reg_aliases in FOREIGN_REGIONS.items():
        for alias in reg_aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', raw_lower):
                canonical = f"{reg_name} (Remote)" if remote_type == "remote" else f"{raw_str} ({reg_name})"
                return {
                    "canonical_location": canonical,
                    "city": raw_str.split(',')[0].strip() if ',' in raw_str else raw_str,
                    "state": None,
                    "country": reg_name,
                    "remote_type": remote_type,
                    "work_modality": "Online" if remote_type == "remote" else "Offline",
                    "is_india": False,
                    "is_worldwide": False,
                    "is_foreign": True
                }

    # Fallback to cleaned raw string
    return {
        "canonical_location": raw_str,
        "city": raw_str.split(',')[0].strip() if ',' in raw_str else raw_str,
        "state": None,
        "country": "Unspecified",
        "remote_type": remote_type,
        "work_modality": "Online" if remote_type == "remote" else "Offline",
        "is_india": False,
        "is_worldwide": False,
        "is_foreign": False
    }


def is_foreign_preference(location_str: str) -> bool:
    """
    Checks if a user's location preference explicitly asks for a foreign region (e.g. USA, UK, Germany).
    """
    loc_lower = str(location_str).lower().strip()
    for reg_name, reg_aliases in FOREIGN_REGIONS.items():
        for alias in reg_aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', loc_lower):
                return True
    return False


def matches_location_preference(job_location: str, preferred_locations: List[str], remote_preferred: bool) -> Tuple[bool, int]:
    """
    Evaluates whether a job satisfies user location/remote preferences with strict geographic localization.
    Returns (matches: bool, score: 0 to 10 points).
    
    Rules:
    1. If user asks for Pune, Bengaluru, or India (or leaves blank for EDITH India context):
       - Jobs in USA, UK, Canada, Europe, or other foreign countries MUST NOT match (False, 0).
       - Remote jobs restricted to USA/foreign regions (e.g. 'Remote (USA)', 'Remote (Europe)') MUST NOT match (False, 0).
    2. If user specifies preferred Indian cities (e.g. Pune, Bengaluru):
       - Exact city match -> (True, 10).
       - Remote within India (e.g. 'India (Remote)') -> (True, 9) if remote_preferred else (False, 2).
       - Truly open Worldwide / Anywhere remote -> (True, 8) if remote_preferred else (False, 2).
       - On-site in other Indian city -> (False, 1).
    3. If user specifies 'India' or no specific city:
       - Indian jobs -> (True, 10).
       - Worldwide remote jobs -> (True, 9) if remote_preferred else (False, 2).
    """
    loc_info = normalize_location(job_location)
    is_remote = loc_info["remote_type"] == "remote" or "remote" in str(job_location).lower()

    # Determine if user explicitly requested a foreign location
    user_wants_foreign = any(is_foreign_preference(p) for p in (preferred_locations or []))

    # If the job is in a foreign country or restricted foreign remote
    if loc_info["is_foreign"]:
        if not user_wants_foreign:
            # Indian / local user did not ask for foreign jobs. This is an explicit mismatch!
            return False, 0
        else:
            # User specifically asked for this foreign location
            for pref in (preferred_locations or []):
                p_lower = pref.lower().strip()
                if p_lower in loc_info["canonical_location"].lower() or p_lower in (loc_info["city"] or "").lower():
                    return True, 10
            return is_remote and remote_preferred, 7 if is_remote else 2

    # If user wants a foreign location, but job is in India
    if user_wants_foreign and loc_info["is_india"]:
        return False, 0

    # Job is in India
    if loc_info["is_india"]:
        if not preferred_locations or all(p.lower().strip() in ["india", "pan india", "anywhere", "remote"] for p in preferred_locations):
            return True, 10

        # User has specified specific cities (e.g. Pune, Bangalore)
        job_city = (loc_info["city"] or "").lower()
        canonical_lower = loc_info["canonical_location"].lower()

        city_matched = False
        for pref in preferred_locations:
            pref_lower = pref.lower().strip()
            if pref_lower in ["remote", "work from home", "anywhere"] and is_remote:
                city_matched = True
                break
            if pref_lower in ["india", "pan india"]:
                city_matched = True
                break
            if job_city and (pref_lower in job_city or job_city in pref_lower):
                city_matched = True
                break
            if pref_lower in canonical_lower:
                city_matched = True
                break
            # Also check aliases in INDIAN_TECH_HUBS
            for hub_key, hub_data in INDIAN_TECH_HUBS.items():
                if pref_lower in hub_data["aliases"]:
                    if job_city == hub_data["canonical"].lower() or any(a in canonical_lower for a in hub_data["aliases"]):
                        city_matched = True
                        break
            if city_matched:
                break

        if city_matched:
            return True, 10

        # If city didn't match, check if it's remote within India and user accepts remote
        if is_remote and remote_preferred:
            return True, 9

        # On-site in a different Indian city
        return False, 1

    # Job is Worldwide / Global remote (open to candidates in India)
    if loc_info["is_worldwide"]:
        if remote_preferred:
            # Good match if remote is accepted
            return True, 8 if preferred_locations else 10
        else:
            # User specifically wanted on-site in a local city
            return False, 2

    # Unspecified location
    if is_remote and remote_preferred:
        return True, 7

    return False, 1
