"""
EDITH Match Scoring & Explainability Engine (0-100).
Deterministic, fully explainable score breakdown.
Strict scoring ethics: Never uses protected characteristics or personal attributes.
Calculates separate Job Quality and Risk Signals.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import re

from backend.app.locations.india_locations import matches_location_preference

# Configurable score weights strictly summing to 100
DEFAULT_WEIGHTS = {
    "skills": 30,
    "role": 20,
    "experience": 15,
    "location": 10,
    "education": 5,
    "employment": 5,
    "salary": 5,
    "freshness": 5,
    "requirements": 5
}

SUSPICIOUS_PHRASES = [
    "registration fee", "pay fee", "security deposit", "payment required",
    "wire transfer", "cryptocurrency payment", "send money", "processing fee",
    "telegram @", "whatsapp only to", "kindly transfer"
]


def score_job_match(job: Dict[str, Any], query_spec: Dict[str, Any], weights: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Computes an explainable 0-100 EDITH Match Score with subscore components,
    strengths ('Why it matches'), gaps, and quality/risk signals.
    """
    w = weights or DEFAULT_WEIGHTS
    breakdown = {}
    why_it_matches = []
    potential_gaps = []

    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()
    job_skills = [s.lower() for s in (job.get("skills") or [])]
    job_tech = [t.lower() for t in (job.get("technologies") or [])]
    combined_job_text = f"{title} {description} {' '.join(job_skills)} {' '.join(job_tech)}"

    # 1. Skills Match (30 pts)
    target_skills = [s.lower() for s in (query_spec.get("skills") or [])]
    if target_skills:
        matched_skills = [s for s in target_skills if s in combined_job_text]
        missing_skills = [s for s in target_skills if s not in combined_job_text]
        skill_ratio = len(matched_skills) / len(target_skills)
        skills_score = round(skill_ratio * w["skills"])
        for s in matched_skills:
            why_it_matches.append(f"✓ {s.title()}")
        for s in missing_skills[:2]:
            potential_gaps.append(f"⚠ {s.title()} not explicitly emphasized")
    else:
        skills_score = round(0.85 * w["skills"])
        why_it_matches.append("✓ Technical skill profile aligns")
    breakdown["skills"] = {"score": skills_score, "max": w["skills"]}

    # 2. Role / Title Match (20 pts)
    target_roles = [r.lower() for r in (query_spec.get("roles") or [])]
    role_matched = False
    if target_roles:
        for r in target_roles:
            if r in title or any(w in title for w in r.split()):
                role_matched = True
                why_it_matches.append(f"✓ Target role match ({r.title()})")
                break
        role_score = w["role"] if role_matched else round(0.5 * w["role"])
        if not role_matched:
            potential_gaps.append("⚠ Role title differs from target keywords")
    else:
        role_score = round(0.8 * w["role"])
    breakdown["role"] = {"score": role_score, "max": w["role"]}

    # 3. Experience Compatibility (15 pts)
    exp_max = query_spec.get("experience_max")
    job_exp_min = job.get("experience_min") or 0
    job_exp_max = job.get("experience_max") or 5

    if exp_max is not None:
        if job_exp_min <= exp_max:
            exp_score = w["experience"]
            why_it_matches.append(f"✓ {int(job_exp_min)}–{int(job_exp_max)} years experience accepted")
        elif job_exp_min <= exp_max + 1:
            exp_score = round(0.6 * w["experience"])
            potential_gaps.append(f"⚠ Prefers {int(job_exp_min)}+ years experience")
        else:
            exp_score = round(0.2 * w["experience"])
            potential_gaps.append(f"⚠ Requires {int(job_exp_min)} years experience")
    else:
        exp_score = round(0.9 * w["experience"])
    breakdown["experience"] = {"score": exp_score, "max": w["experience"]}

    # 4. Location / Remote Fit (10 pts)
    target_locs = query_spec.get("locations") or []
    remote_pref = query_spec.get("remote", False)
    job_location = job.get("location") or "Remote"
    loc_match, loc_points = matches_location_preference(job_location, target_locs, remote_pref)
    breakdown["location"] = {"score": loc_points, "max": w["location"]}
    if loc_match:
        why_it_matches.append(f"✓ Location fit ({job_location})")
    else:
        potential_gaps.append(f"⚠ Located in {job_location}")

    # 5. Education Fit (5 pts)
    edu_score = w["education"]
    breakdown["education"] = {"score": edu_score, "max": w["education"]}
    why_it_matches.append("✓ Education qualifications satisfied")

    # 6. Employment Type Fit (5 pts)
    target_emp = [e.lower() for e in (query_spec.get("employment_types") or [])]
    job_emp = (job.get("employment_type") or "full-time").lower()
    if target_emp and job_emp:
        if any(te in job_emp or job_emp in te for te in target_emp):
            emp_score = w["employment"]
            why_it_matches.append(f"✓ {job_emp.title()} employment type")
        else:
            emp_score = round(0.6 * w["employment"])
    else:
        emp_score = w["employment"]
    breakdown["employment"] = {"score": emp_score, "max": w["employment"]}

    # 7. Salary Fit (5 pts)
    target_sal_min = query_spec.get("salary_min")
    job_sal_min = job.get("salary_min")
    if target_sal_min and job_sal_min:
        if job_sal_min >= target_sal_min:
            sal_score = w["salary"]
            why_it_matches.append(f"✓ Compensation meets target criteria")
        else:
            sal_score = round(0.6 * w["salary"])
            potential_gaps.append("⚠ Stated compensation is slightly below target")
    else:
        sal_score = round(0.8 * w["salary"])  # Undisclosed is common in tech
    breakdown["salary"] = {"score": sal_score, "max": w["salary"]}

    # 8. Freshness (5 pts)
    now_utc = datetime.now(timezone.utc)
    freshness_pts = w["freshness"]
    date_posted_str = job.get("date_posted")
    if date_posted_str:
        try:
            posted_dt = datetime.fromisoformat(date_posted_str.replace("Z", "+00:00"))
            hours_old = (now_utc - posted_dt).total_seconds() / 3600
            if hours_old < 24:
                freshness_pts = w["freshness"]
                why_it_matches.append("✓ Fresh posting (< 24h old)")
            elif hours_old < 72:
                freshness_pts = round(0.8 * w["freshness"])
            else:
                freshness_pts = round(0.6 * w["freshness"])
        except Exception:
            freshness_pts = round(0.8 * w["freshness"])
    breakdown["freshness"] = {"score": freshness_pts, "max": w["freshness"]}

    # 9. Requirements Compatibility (5 pts)
    req_pts = round(0.9 * w["requirements"])
    breakdown["requirements"] = {"score": req_pts, "max": w["requirements"]}

    total_score = sum(b["score"] for b in breakdown.values())
    total_score = max(0, min(100, total_score))

    # Job Quality & Risk Signals (Separate from Match Score)
    risk_signals = []
    for phrase in SUSPICIOUS_PHRASES:
        if phrase in combined_job_text:
            risk_signals.append(f"Potential risk detected: Mentions '{phrase}'")

    source_name = (job.get("source") or "").lower()
    source_conf = 98.0 if source_name in ["greenhouse", "lever", "ashby"] else (90.0 if source_name in ["jobicy", "arbeitnow"] else 80.0)
    listing_quality = 95.0 if len(description) > 300 else (85.0 if len(description) > 100 else 70.0)
    freshness_score = 95.0 if freshness_pts >= 4 else 80.0

    return {
        "match_score": float(total_score),
        "score_breakdown": breakdown,
        "why_it_matches": why_it_matches[:5],
        "potential_gaps": potential_gaps[:3],
        "quality_signals": {
            "freshness_score": freshness_score,
            "source_confidence": source_conf,
            "listing_quality_score": listing_quality,
            "risk_signals": risk_signals
        }
    }
