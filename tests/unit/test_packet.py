"""
Unit Tests for Application Packet Builder Module
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 3.1, FR-09, Section 4.2
"""

import json
from datetime import datetime
from tools.schemas import (
    Listing,
    Profile,
    Education,
    Project,
    EvidenceFact,
    ApplicationDraft,
    ClaimAudit,
    ClaimStatus,
    ScoreBreakdown,
)
from tools.packet import (
    build_application_packet,
    export_packet_markdown,
    export_packet_json,
    export_packet_text,
)


def test_build_application_packet():
    profile = Profile(
        profile_id="prof_01",
        full_name="Sadiqua Parween",
        email="falaksadiqua786@gmail.com",
        phone="+91 9876543210",
        education=[
            Education(
                degree="B.Tech Computer Science",
                institution="S-VYASA University",
                graduation_year=2026,
                cgpa=8.9,
            )
        ],
        skills=["Python", "Machine Learning", "Git"],
        projects=[
            Project(
                title="InternIQ Assistant",
                description="Built automated internship assistant in Python.",
                skills_used=["Python", "LangGraph"],
            )
        ],
        confirmed_facts=[],
    )

    listing = Listing(
        listing_id="opp_100",
        source_id="greenhouse",
        source_record_id="gh_100",
        canonical_url="https://boards.greenhouse.io/corp/jobs/100",
        title="AI Engineering Intern",
        organization="Tech Corp",
        description="Develop deep learning models.",
        deadline="2026-12-01",
    )

    draft = ApplicationDraft(
        draft_id="draft_100",
        opportunity_id="opp_100",
        profile_id="prof_01",
        version=1,
        tailored_resume_bullets=[
            "Developed machine learning models using Python and PyTorch.",
            "Designed data ingestion pipeline handling structured feeds.",
        ],
        cover_letter="Dear Hiring Team,\n\nI am excited to apply for the AI Engineering Intern role at Tech Corp...",
        claims=[
            ClaimAudit(
                claim_id="c1",
                claim_text="Experienced in Python",
                claim_type="skill",
                status=ClaimStatus.SUPPORTED,
                supporting_fact_ids=["fact_python"],
            )
        ],
        is_fully_grounded=True,
    )

    score = ScoreBreakdown(
        total_score=0.88,
        factor_scores={"skills": 0.9, "semantic": 0.85, "preference": 0.9, "deadline": 0.8},
        weights_used={"skills": 0.35, "semantic": 0.35, "preference": 0.20, "deadline": 0.10},
        evidence_coverage=1.0,
        missing_skills=["Kubernetes"],
    )

    packet = build_application_packet(listing, profile, draft, score_breakdown=score)

    assert packet["opportunity_id"] == "opp_100"
    assert packet["title"] == "AI Engineering Intern"
    assert packet["organization"] == "Tech Corp"
    assert packet["canonical_application_url"] == "https://boards.greenhouse.io/corp/jobs/100"
    assert packet["applicant"]["full_name"] == "Sadiqua Parween"
    assert packet["claims_audit_summary"]["is_fully_grounded"] is True
    assert packet["claims_audit_summary"]["total_claims"] == 1
    assert "Automatic application submission is disabled" in packet["human_control_notice"]

    # Test Markdown export
    md_output = export_packet_markdown(packet)
    assert "# Application Packet: AI Engineering Intern at Tech Corp" in md_output
    assert "Sadiqua Parween" in md_output
    assert "Automatic application submission is disabled" in md_output

    # Test JSON export
    json_output = export_packet_json(packet)
    parsed = json.loads(json_output)
    assert parsed["opportunity_id"] == "opp_100"

    # Test Plaintext export
    txt_output = export_packet_text(packet)
    assert "INTERNSHIP APPLICATION PACKET" in txt_output
    assert "https://boards.greenhouse.io/corp/jobs/100" in txt_output
