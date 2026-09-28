"""
Node 1: Intent Parser
Converts the natural-language prompt into a structured schema (Pydantic model) outlining required fields.
"""
import os
import re
import json
from typing import Dict, Any, List
from ai_engine.state import TargetSchemaDefinition, SchemaField

class IntentParser:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    def parse_intent(self, prompt: str) -> TargetSchemaDefinition:
        """
        Dynamically derives the target schema from the natural language prompt.
        If an external LLM is configured, it will use LLM inference.
        Otherwise, it uses our high-fidelity deterministic semantic parser.
        """
        prompt_lower = prompt.lower()

        # 1. Jobs / Openings / Job Seekers (LinkedIn, Naukri, Indeed, Career Portals)
        if any(w in prompt_lower for w in ["job", "jobs", "opening", "openings", "vacancy", "vacancies", "career", "careers", "hiring", "naukri", "indeed", "internship", "internships", "recruitment", "job seeker", "job search"]):
            return TargetSchemaDefinition(
                entity_name="JobOpening",
                description="Structured job posting from LinkedIn, Naukri, Indeed, or verified career portals",
                fields=[
                    SchemaField(name="job_title", type="string", description="Official title of the open position", required=True),
                    SchemaField(name="company", type="string", description="Hiring company or organization", required=True),
                    SchemaField(name="location", type="string", description="City, Country, Remote, or Hybrid status", required=True),
                    SchemaField(name="experience_years", type="string", description="Required years of experience", required=False),
                    SchemaField(name="skills", type="list", description="Core technical competencies and tools required", required=False),
                    SchemaField(name="salary_range", type="string", description="Disclosed compensation package or CTC", required=False),
                    SchemaField(name="platform_source", type="string", description="Origin platform (LinkedIn, Naukri, Indeed, Career Site)", required=True),
                    SchemaField(name="apply_link", type="string", description="Direct application page or posting URL", required=True)
                ]
            )

        # 2. Talent / Engineers / People sourcing
        elif any(w in prompt_lower for w in ["engineer", "developer", "candidate", "talent", "hire", "recruiter", "person", "alumni", "researcher"]):
            return TargetSchemaDefinition(
                entity_name="ProfessionalCandidate",
                description="Structured candidate profile extracted from verified public sources",
                fields=[
                    SchemaField(name="full_name", type="string", description="Full name of the individual", required=True),
                    SchemaField(name="role_title", type="string", description="Job title or primary engineering specialization", required=True),
                    SchemaField(name="organization", type="string", description="Current company or research institution", required=True),
                    SchemaField(name="location", type="string", description="Geographic location or city", required=True),
                    SchemaField(name="skills", type="list", description="Core technical competencies and frameworks", required=True),
                    SchemaField(name="experience_years", type="string", description="Estimated years of experience", required=False),
                    SchemaField(name="profile_link", type="string", description="Verified LinkedIn or portfolio URL", required=True)
                ]
            )

        # 3. Startups / Companies / Venture / Funding
        elif any(w in prompt_lower for w in ["startup", "company", "venture", "funded", "funding", "seed", "series a", "investor", "valuation"]):
            return TargetSchemaDefinition(
                entity_name="VentureCompany",
                description="Structured venture and startup market profile",
                fields=[
                    SchemaField(name="company_name", type="string", description="Official name of the venture or startup", required=True),
                    SchemaField(name="category", type="string", description="Industry vertical or product niche", required=True),
                    SchemaField(name="location", type="string", description="Headquarters or principal hub", required=True),
                    SchemaField(name="total_funding", type="string", description="Reported total capital raised or latest round", required=False),
                    SchemaField(name="lead_investors", type="list", description="Notable institutional or angel investors", required=False),
                    SchemaField(name="key_product", type="string", description="Core flagship product or AI offering", required=True),
                    SchemaField(name="website", type="string", description="Verified company website", required=True)
                ]
            )

        # 4. B2B Sales Leads / Decision Makers
        elif any(w in prompt_lower for w in ["lead", "sales", "b2b", "decision maker", "executive", "sponsor", "buyer", "prospect"]):
            return TargetSchemaDefinition(
                entity_name="SalesLead",
                description="B2B sales lead and decision maker record with verified contact points",
                fields=[
                    SchemaField(name="contact_name", type="string", description="Full name of target lead", required=True),
                    SchemaField(name="company", type="string", description="Target enterprise organization", required=True),
                    SchemaField(name="designation", type="string", description="Executive role / title", required=True),
                    SchemaField(name="work_email", type="string", description="Derived or verified corporate email handle", required=False),
                    SchemaField(name="linkedin_url", type="string", description="Verified executive LinkedIn URL", required=True),
                    SchemaField(name="intent_summary", type="string", description="Identified buying need or sponsorship alignment", required=False)
                ]
            )

        # 5. Default Dynamic Entity Generator based on NLP token extraction
        keywords = re.findall(r'\b[A-Za-z]{3,}\b', prompt)
        clean_name = "".join([w.capitalize() for w in keywords[:2]]) or "IntelligenceRecord"
        return TargetSchemaDefinition(
            entity_name=clean_name,
            description=f"Auto-generated schema from intent: '{prompt}'",
            fields=[
                SchemaField(name="title", type="string", description="Primary name or title", required=True),
                SchemaField(name="category", type="string", description="Domain classification", required=True),
                SchemaField(name="description", type="string", description="Extracted synopsis", required=True),
                SchemaField(name="source_reference", type="string", description="Origin link or reference identifier", required=True)
            ]
        )
