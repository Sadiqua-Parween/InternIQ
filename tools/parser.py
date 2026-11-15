"""
Resume and Profile Parsing Module
Owner: Sadiqua Parween (Team HumanBot)
Status: Interface Stub & Fallback Parser

Implements tool contract for `parse_profile`:
File bytes / text -> Profile + evidence / confidence
"""

from typing import Optional
from datetime import datetime
from tools.schemas import Profile, Education, Skill, Project, EvidenceFact


def parse_profile(file_content: bytes, filename: str, profile_id: str = "prof_default") -> Profile:
    """
    Parses resume document (PDF, DOCX, or text) into a validated Profile model.
    Preserves source evidence snippets for each atomic fact.
    
    Teammate implementation note:
    Extract text using pypdf / python-docx, extract structured fields,
    and populate confirmed_facts with atomic evidence facts.
    """
    # Safe fallback/initial implementation
    return Profile(
        profile_id=profile_id,
        full_name="Candidate",
        email="candidate@example.edu",
        education=[
            Education(
                degree="B.Tech Computer Science & Engineering",
                institution="University",
                graduation_year=2026,
                cgpa=8.5,
                is_verified=True,
            )
        ],
        skills=["Python", "Machine Learning", "Git"],
        projects=[
            Project(
                title="Academic Project",
                description="Built machine learning pipeline in Python",
                skills_used=["Python", "Machine Learning"],
            )
        ],
        confirmed_facts=[
            EvidenceFact(
                fact_id=f"{profile_id}_f1",
                fact_type="skill",
                text="Proficient in Python programming",
                source_doc=filename,
                confidence=1.0,
                confirmed_by_user=True,
            ),
            EvidenceFact(
                fact_id=f"{profile_id}_f2",
                fact_type="education",
                text="Graduating in year 2026 with B.Tech CSE",
                source_doc=filename,
                confidence=1.0,
                confirmed_by_user=True,
            ),
        ],
        updated_at=datetime.utcnow(),
    )
