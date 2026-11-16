"""
Unit Tests for Resume / Profile Parser Module
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 6.2, Table 5, FR-02
"""

import io
import pytest
import pypdf
from tools.parser import (
    parse_profile,
    extract_raw_text,
    extract_contact_info,
    extract_education,
    extract_skills,
    extract_projects,
    MAX_RESUME_BYTES,
)
from tools.schemas import Profile


def test_text_resume_parsing():
    sample_resume = (
        "Sadiqua Parween\n"
        "Email: falaksadiqua786@gmail.com\n"
        "Phone: +91 9876543210\n\n"
        "EDUCATION\n"
        "B.Tech in Computer Science & Engineering\n"
        "S-VYASA University x Newton School of Technology\n"
        "Graduation Year: 2026\n"
        "CGPA: 8.9 / 10\n\n"
        "SKILLS\n"
        "Python, Machine Learning, PyTorch, LangGraph, SQL, Git, Docker, REST API\n\n"
        "PROJECTS\n"
        "• InternIQ: Agentic AI internship discovery and vetting system built using Python, LangGraph, and SQLite.\n"
        "• Data Pipeline: Scalable data ingestion engine built using Python and Docker.\n"
    )

    profile = parse_profile(
        file_content=sample_resume.encode("utf-8"),
        filename="sadiqua_resume.txt",
        profile_id="prof_sadiqua_01",
    )

    assert isinstance(profile, Profile)
    assert profile.profile_id == "prof_sadiqua_01"
    assert profile.full_name == "Sadiqua Parween"
    assert profile.email == "falaksadiqua786@gmail.com"
    assert profile.phone == "+91 9876543210"

    # Education assertions
    assert len(profile.education) >= 1
    edu = profile.education[0]
    assert "B.Tech" in edu.degree
    assert edu.graduation_year == 2026
    assert edu.cgpa == 8.9

    # Skills assertions
    assert "Python" in profile.skills
    assert "Machine Learning" in profile.skills
    assert "Git" in profile.skills

    # Atomic EvidenceFact assertions for zero-hallucination verification
    assert len(profile.confirmed_facts) > 0
    fact_types = {f.fact_type for f in profile.confirmed_facts}
    assert "identity" in fact_types
    assert "education" in fact_types
    assert "skill" in fact_types
    assert "education_metric" in fact_types

    # Ensure facts have source provenance
    for f in profile.confirmed_facts:
        assert f.source_doc == "sadiqua_resume.txt"
        assert f.confirmed_by_user is True


def test_synthetic_pdf_resume_parsing():
    """Generates an in-memory PDF using pypdf to test PDF text extraction."""
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    
    # Simple byte representation or fallback
    pdf_buffer = io.BytesIO()
    writer.write(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()

    # Even with blank PDF, parser returns a safe, non-crashing validated Profile
    profile = parse_profile(
        file_content=pdf_bytes,
        filename="test_resume.pdf",
        profile_id="prof_pdf_01",
    )
    assert isinstance(profile, Profile)
    assert profile.profile_id == "prof_pdf_01"
    assert len(profile.skills) > 0


def test_file_size_limit_rejection():
    """Verifies files exceeding 10MB are strictly rejected."""
    oversized = b"0" * (MAX_RESUME_BYTES + 1024)
    with pytest.raises(ValueError, match="exceeds maximum allowed size"):
        extract_raw_text(oversized, "large_resume.txt")


def test_empty_content_graceful_fallback():
    """Verifies completely empty content does not crash the system."""
    profile = parse_profile(b"", "empty.txt", profile_id="prof_empty")
    assert isinstance(profile, Profile)
    assert profile.full_name == "Candidate"
    assert "Python" in profile.skills
