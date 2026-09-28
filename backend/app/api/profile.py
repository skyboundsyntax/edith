"""
User Profile Management for Job Seekers.
Allows optional candidate profile creation to enable personalized profile matching.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.db.database import get_db
from backend.app.db.models import UserProfileModel

router = APIRouter(prefix="/profile", tags=["Profile"])

class UserProfileRequest(BaseModel):
    name: Optional[str] = "Job Seeker"
    email: Optional[str] = None
    skills: List[str] = []
    experience_years: float = 0.0
    education: Optional[str] = None
    preferred_roles: List[str] = []
    preferred_locations: List[str] = []
    remote_preference: bool = True
    salary_expectation: Optional[float] = None
    employment_preferences: List[str] = []
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None

@router.get("")
def get_user_profile(db: Session = Depends(get_db)):
    profile = db.query(UserProfileModel).first()
    if not profile:
        return {
            "exists": False,
            "profile": None
        }
    return {
        "exists": True,
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "skills": profile.skills,
            "experience_years": profile.experience_years,
            "education": profile.education,
            "preferred_roles": profile.preferred_roles,
            "preferred_locations": profile.preferred_locations,
            "remote_preference": profile.remote_preference,
            "salary_expectation": profile.salary_expectation,
            "portfolio_url": profile.portfolio_url,
            "github_url": profile.github_url,
            "linkedin_url": profile.linkedin_url
        }
    }

@router.post("")
def save_user_profile(req: UserProfileRequest, db: Session = Depends(get_db)):
    profile = db.query(UserProfileModel).first()
    if not profile:
        profile = UserProfileModel(
            id="profile_default",
            created_at=datetime.now(timezone.utc)
        )
        db.add(profile)

    profile.name = req.name
    profile.email = req.email
    profile.skills = req.skills
    profile.experience_years = req.experience_years
    profile.education = req.education
    profile.preferred_roles = req.preferred_roles
    profile.preferred_locations = req.preferred_locations
    profile.remote_preference = req.remote_preference
    profile.salary_expectation = req.salary_expectation
    profile.employment_preferences = req.employment_preferences
    profile.portfolio_url = req.portfolio_url
    profile.github_url = req.github_url
    profile.linkedin_url = req.linkedin_url
    profile.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(profile)

    return {"status": "saved", "profile_id": profile.id}
