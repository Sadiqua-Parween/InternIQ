"""
Unit Tests for Hybrid Matching & Transparent Ranking Engine
Owner: Mohd Faizan Khan (Team HumanBot)
"""

import pytest
from datetime import date
from tools.schemas import Listing, Profile, Education, Preference, WorkMode
from tools.ranker import (
    calculate_skills_factor,
    calculate_preference_factor,
    calculate_deadline_factor,
    score_opportunity,
    rank_opportunities,
    DEFAULT_WEIGHTS,
)


@pytest.fixture
def candidate_profile():
    return Profile(
        profile_id="prof_001",
        full_name="Mohd Faizan Khan",
        email="faizan@example.edu",
        education=[
            Education(
                degree="B.Tech Computer Science",
                institution="S-VYASA University",
                graduation_year=2026,
                cgpa=8.8,
            )
        ],
        skills=["Python", "Machine Learning", "PyTorch", "SQL", "Git"],
    )


@pytest.fixture
def candidate_preference():
    return Preference(
        profile_id="prof_001",
        target_roles=["Machine Learning Intern", "AI Engineer"],
        domains=["Artificial Intelligence", "Machine Learning"],
        locations=["Bangalore"],
        work_modes=[WorkMode.REMOTE, WorkMode.HYBRID],
        min_stipend=25000.0,
    )


def test_skills_factor_calculation(candidate_profile):
    """Checks skill matching, missing skills, and evidence coverage."""
    listing = Listing(
        listing_id="list_01",
        source_id="greenhouse",
        source_record_id="1",
        canonical_url="https://careers.example.com/1",
        title="ML Intern",
        organization="AI Corp",
        description="Machine learning role.",
        required_skills=["Python", "PyTorch", "Kubernetes", "Docker"],
    )
    score, matched, missing, coverage = calculate_skills_factor(listing, candidate_profile)
    assert score == 0.5  # 2 out of 4 skills matched (Python, PyTorch)
    assert "Python" in matched
    assert "PyTorch" in matched
    assert "Kubernetes" in missing
    assert "Docker" in missing
    assert coverage == 0.5


def test_skills_factor_empty_required_skills(candidate_profile):
    """When listing has no required skills, factor is None."""
    listing = Listing(
        listing_id="list_empty_skills",
        source_id="greenhouse",
        source_record_id="2",
        canonical_url="https://careers.example.com/2",
        title="General Intern",
        organization="Corp",
        description="General exploratory role.",
        required_skills=[],
    )
    score, matched, missing, coverage = calculate_skills_factor(listing, candidate_profile)
    assert score is None
    assert matched == []
    assert missing == []


def test_preference_factor_evaluation(candidate_preference):
    """Checks preference fit against assessable fields."""
    listing = Listing(
        listing_id="list_pref",
        source_id="lever",
        source_record_id="3",
        canonical_url="https://jobs.example.com/3",
        title="Machine Learning Intern",
        organization="Acme AI",
        description="Working in Artificial Intelligence domain.",
        locations=["Bangalore"],
        work_mode=WorkMode.HYBRID,
        stipend=30000.0,
    )
    score, explanations = calculate_preference_factor(listing, candidate_preference)
    assert score == 1.0  # All 5 assessable preferences satisfied
    assert any("Role match" in e for e in explanations)
    assert any("Stipend match" in e for e in explanations)


def test_deadline_urgency_factor():
    """Checks Table 7 formula: D = 1 - min(days_remaining / 30, 1)."""
    ref_date = date(2026, 11, 15)
    listing_soon = Listing(
        listing_id="list_soon",
        source_id="csv",
        source_record_id="4",
        canonical_url="https://example.com/4",
        title="Role 1",
        organization="Org",
        description="Desc",
        deadline="2026-11-25",  # 10 days left
    )
    urgency, expl = calculate_deadline_factor(listing_soon, current_date=ref_date)
    # 1 - 10/30 = 0.6667
    assert pytest.approx(urgency, 0.01) == 0.67

    listing_far = Listing(
        listing_id="list_far",
        source_id="csv",
        source_record_id="5",
        canonical_url="https://example.com/5",
        title="Role 2",
        organization="Org",
        description="Desc",
        deadline="2026-12-30",  # 45 days left -> capped at 30
    )
    urgency_far, _ = calculate_deadline_factor(listing_far, current_date=ref_date)
    assert urgency_far == 0.0  # 1 - min(45/30, 1) = 0.0


def test_weight_renormalization_missing_factors(candidate_profile, candidate_preference):
    """When a factor like deadline is missing, weights renormalize to sum to 1.0."""
    listing_no_deadline = Listing(
        listing_id="list_no_dl",
        source_id="csv",
        source_record_id="6",
        canonical_url="https://example.com/6",
        title="Machine Learning Intern",
        organization="OpenAI Lab",
        description="Research in machine learning and deep learning models.",
        required_skills=["Python", "Machine Learning"],
        deadline=None,  # Missing deadline
    )
    sb = score_opportunity(listing_no_deadline, candidate_profile, candidate_preference)
    assert sb.factor_scores["deadline"] is None
    assert "deadline" not in sb.weights_used
    assert pytest.approx(sum(sb.weights_used.values()), 0.001) == 1.0
    assert sb.total_score is not None
    assert 0.0 <= sb.total_score <= 1.0


def test_ranking_sorts_descending(candidate_profile, candidate_preference):
    """High match opportunity should rank ahead of low match opportunity."""
    best_match = Listing(
        listing_id="best_match",
        source_id="greenhouse",
        source_record_id="10",
        canonical_url="https://example.com/best",
        title="Machine Learning Intern",
        organization="Premier AI",
        description="Artificial Intelligence research in Python and PyTorch.",
        locations=["Bangalore"],
        work_mode=WorkMode.HYBRID,
        required_skills=["Python", "Machine Learning", "PyTorch"],
        stipend=40000.0,
        deadline="2026-11-25",
    )
    low_match = Listing(
        listing_id="low_match",
        source_id="manual_csv",
        source_record_id="11",
        canonical_url="https://example.com/low",
        title="Marketing Content Intern",
        organization="Retail Shop",
        description="Write blog posts and create social media banners.",
        locations=["Delhi"],
        work_mode=WorkMode.ON_SITE,
        required_skills=["Photoshop", "Content Writing"],
        stipend=5000.0,
        deadline="2026-12-30",
    )
    ranked = rank_opportunities(
        [low_match, best_match],
        candidate_profile,
        candidate_preference,
        current_date=date(2026, 11, 15),
    )
    assert ranked[0][0].listing_id == "best_match"
    assert ranked[1][0].listing_id == "low_match"
    assert ranked[0][1].total_score > ranked[1][1].total_score
