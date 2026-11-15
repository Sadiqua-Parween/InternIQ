"""
Unit Tests for Profile-Grounded Document Generation & Claim Verifier
Owner: Mohd Faizan Khan (Team HumanBot)
"""

import pytest
from tools.schemas import (
    Listing,
    Profile,
    Education,
    Project,
    EvidenceFact,
    WorkMode,
    ClaimStatus,
    ApplicationDraft,
)
from agent.verifier import ClaimVerifier
from tools.docgen import generate_application_draft


@pytest.fixture
def candidate_profile():
    return Profile(
        profile_id="prof_001",
        full_name="Mohd Faizan Khan",
        email="faizan@example.edu",
        education=[
            Education(
                degree="B.Tech Computer Science & Engineering",
                institution="S-VYASA University",
                graduation_year=2026,
                cgpa=8.8,
            )
        ],
        skills=["Python", "Machine Learning", "PyTorch", "SQL", "Git"],
        projects=[
            Project(
                title="Agentic Workflow Orchestrator",
                description="Built an autonomous multi-agent system in Python and LangGraph with automated verification",
                skills_used=["Python", "LangGraph", "Git"],
            )
        ],
        confirmed_facts=[
            EvidenceFact(
                fact_id="fact_python_01",
                fact_type="skill",
                text="Proficient in Python and machine learning pipelines",
                source_doc="resume.pdf",
                confidence=1.0,
                confirmed_by_user=True,
            ),
            EvidenceFact(
                fact_id="fact_proj_01",
                fact_type="project_achievement",
                text="Engineered an agentic workflow in Python with verifiable deterministic checks",
                source_doc="resume.pdf",
                confidence=1.0,
                confirmed_by_user=True,
            ),
        ],
    )


@pytest.fixture
def sample_listing():
    return Listing(
        listing_id="opp_ml_01",
        source_id="greenhouse",
        source_record_id="gh_99",
        canonical_url="https://example.com/ml-intern",
        title="Machine Learning Intern",
        organization="Nova AI Labs",
        description="Develop deep learning models and agentic workflows in Python.",
        locations=["Bangalore"],
        work_mode=WorkMode.HYBRID,
        required_skills=["Python", "Machine Learning"],
    )


def test_grounded_generation_produces_zero_unsupported_claims(sample_listing, candidate_profile):
    """Clean generation produces 100% grounded materials with zero unsupported claims."""
    draft = generate_application_draft(sample_listing, candidate_profile)
    assert draft.is_fully_grounded
    assert draft.unsupported_claim_count == 0
    assert len(draft.tailored_resume_bullets) > 0
    assert "Nova AI Labs" in draft.cover_letter
    assert "Mohd Faizan Khan" in draft.cover_letter

    # Ensure all claims in audit trail are supported
    for claim in draft.claims:
        assert claim.status in (ClaimStatus.SUPPORTED, ClaimStatus.AMBIGUOUS)


def test_adversarial_hallucination_detected_and_repaired(sample_listing, candidate_profile):
    """
    When an ungrounded claim is injected (e.g. claiming Rust and 99.9% uptime),
    the ClaimVerifier flags it as UNSUPPORTED and the generator repairs it.
    """
    fake_claim = "Led enterprise distributed cluster in Rust with 99.9% uptime"
    draft = generate_application_draft(
        sample_listing,
        candidate_profile,
        max_regeneration_attempts=2,
        adversarial_unsupported_text=fake_claim,
    )
    # The repair loop should have eliminated the fake claim across attempts
    assert fake_claim not in draft.tailored_resume_bullets
    assert draft.is_fully_grounded
    assert draft.unsupported_claim_count == 0


def test_claim_verifier_flags_unsupported_technical_skill(candidate_profile):
    """Direct verifier test: claiming Golang/Docker when not in profile facts -> UNSUPPORTED."""
    verifier = ClaimVerifier(candidate_profile)
    sentence = "Designed backend microservices in Go and deployed with Docker containers."
    audit = verifier.verify_sentence(sentence, claim_id="test_c1")
    assert audit.status == ClaimStatus.UNSUPPORTED
    assert "go" in audit.audit_note.lower() or "docker" in audit.audit_note.lower()
