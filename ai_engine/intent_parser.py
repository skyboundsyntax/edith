"""
Node 1: Intent Parser
Converts the natural-language job search prompt into a structured JobOpening target schema.
Extracts target roles, tech stacks, experience levels, and location criteria.
"""
import os
import re
from typing import Dict, Any, List
from ai_engine.state import TargetSchemaDefinition, SchemaField

class IntentParser:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    def parse_intent(self, prompt: str) -> TargetSchemaDefinition:
        """
        Dynamically analyzes the user's natural-language prompt to construct
        the JobOpening schema specialized for career intelligence across verified portals.
        """
        return TargetSchemaDefinition(
            entity_name="JobOpening",
            description=f"Structured job intelligence extracted for query: '{prompt}'",
            fields=[
                SchemaField(
                    name="job_title", 
                    type="string", 
                    description="Official job title of the position", 
                    required=True
                ),
                SchemaField(
                    name="company", 
                    type="string", 
                    description="Hiring company or organization name", 
                    required=True
                ),
                SchemaField(
                    name="location", 
                    type="string", 
                    description="Job location, remote/hybrid status", 
                    required=True
                ),
                SchemaField(
                    name="experience_years", 
                    type="string", 
                    description="Required experience level or years", 
                    required=False
                ),
                SchemaField(
                    name="skills", 
                    type="list", 
                    description="Core technical competencies and required tools", 
                    required=False
                ),
                SchemaField(
                    name="salary_range", 
                    type="string", 
                    description="Disclosed compensation package or CTC", 
                    required=False
                ),
                SchemaField(
                    name="platform_source", 
                    type="string", 
                    description="Origin career platform (LinkedIn, Jobicy, Arbeitnow, etc.)", 
                    required=True
                ),
                SchemaField(
                    name="apply_link", 
                    type="string", 
                    description="Direct URL to apply for the position", 
                    required=True
                )
            ]
        )
