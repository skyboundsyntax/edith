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
        "aliases": ["bengaluru", "bangalore", "blr", "whitefield", "electronic city", "koramangala", "bellandur"]
    },
    "pune": {
        "canonical": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "aliases": ["pune", "hinjewadi", "magarpatta", "viman nagar", "baner", "wakad", "kharadi"]
    },
    "mumbai": {
        "canonical": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "aliases": ["mumbai", "bombay", "navi mumbai", "thane", "bkc", "andheri", "powai"]
    },
    "hyderabad": {
        "canonical": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "aliases": ["hyderabad", "secunderabad", "hitech city", "gachibowli", "madhapur", "kondapur", "hyd"]
    },
    "chennai": {
        "canonical": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "aliases": ["chennai", "madras", "omr", "t nagar", "guindy", "velachery"]
    },
    "delhi_ncr": {
        "canonical": "Delhi NCR",
        "state": "Delhi NCR",
        "country": "India",
        "aliases": ["delhi", "new delhi", "delhi ncr", "ncr", "connaught place"]
    },
    "gurgaon": {
        "canonical": "Gurgaon",
        "state": "Haryana",
        "country": "India",
        "aliases": ["gurgaon", "gurugram", "cyber city", "sohna road", "golf course road", "udyog vihar"]
    },
    "noida": {
        "canonical": "Noida",
        "state": "Uttar Pradesh",
        "country": "India",
        "aliases": ["noida", "greater noida", "sector 62", "sector 18", "sector 125"]
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
    }
}

REMOTE_KEYWORDS = [
    "remote", "work from home", "wfh", "anywhere", "telecommute", "distributed", "virtual"
]

HYBRID_KEYWORDS = [
    "hybrid", "flexible", "partial remote", "2-3 days remote"
]


def normalize_location(raw_location: str) -> Dict[str, Optional[str]]:
    """
    Normalizes any raw location string into canonical city, state, country, and remote type.
    """
    if not raw_location or not raw_location.strip():
        return {
            "canonical_location": "Remote / Unspecified",
            "city": None,
            "state": None,
            "country": "India",
            "remote_type": "remote"
        }

    raw_lower = raw_location.lower().strip()
    
    # Detect remote/hybrid
    remote_type = "on-site"
    if any(k in raw_lower for k in REMOTE_KEYWORDS):
        remote_type = "remote"
    elif any(k in raw_lower for k in HYBRID_KEYWORDS):
        remote_type = "hybrid"

    # Match Indian tech hub
    matched_hub = None
    for hub_key, hub_data in INDIAN_TECH_HUBS.items():
        for alias in hub_data["aliases"]:
            # word boundary search to avoid accidental substring matches
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
            "remote_type": remote_type
        }

    # Check for general India match
    if "india" in raw_lower or "in" == raw_lower or "/in" in raw_lower:
        return {
            "canonical_location": "India (Remote)" if remote_type == "remote" else "India",
            "city": None,
            "state": None,
            "country": "India",
            "remote_type": remote_type
        }

    # Fallback to cleaned raw string
    return {
        "canonical_location": raw_location.strip(),
        "city": raw_location.split(',')[0].strip() if ',' in raw_location else raw_location.strip(),
        "state": None,
        "country": "India" if "india" in raw_lower else "Global",
        "remote_type": remote_type
    }


def matches_location_preference(job_location: str, preferred_locations: List[str], remote_preferred: bool) -> Tuple[bool, int]:
    """
    Evaluates whether a job satisfies user location/remote preferences.
    Returns (matches: bool, score: 0 to 10 points).
    """
    if not preferred_locations and not remote_preferred:
        return True, 10

    loc_info = normalize_location(job_location)
    is_remote = loc_info["remote_type"] == "remote" or "remote" in str(job_location).lower()

    if remote_preferred and is_remote:
        return True, 10

    if not preferred_locations:
        return True, 8 if is_remote else 6

    # Compare with preferred locations
    job_city = (loc_info["city"] or "").lower()
    canonical_lower = loc_info["canonical_location"].lower()

    for pref in preferred_locations:
        pref_lower = pref.lower().strip()
        if pref_lower in ["remote", "work from home", "anywhere"] and is_remote:
            return True, 10
        if pref_lower in ["india", "pan india"] and loc_info["country"] == "India":
            return True, 10
        if job_city and pref_lower in job_city:
            return True, 10
        if pref_lower in canonical_lower:
            return True, 10

    # If job is remote and user also accepted remote
    if is_remote:
        return True, 8

    return False, 2
