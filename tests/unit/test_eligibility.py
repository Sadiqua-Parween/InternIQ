"""
Unit Tests for Deterministic Eligibility Verification Engine
Owner: Mohd Faizan Khan (Team HumanBot)
"""

import pytest
from datetime import date
from tools.schemas import (
    Listing,
    Profile,
    Education,
    Preference,
    WorkMode,
    EligibilityVerdict,
)
from tools.eligibility import check_eligibility


@pytest.fixture
def base_profile():
    return Profile(
        profile_id="prof_faizan",
        full_name="Mohd Faizan Khan",
        email="faizan@example.edu",
        education=[
            Education(
                degree="B.Tech Computer Science & Engineering",
                institution="S-VYASA University",
                branch="Computer Science",
                graduation_year=2026,
                cgpa=8.8,
                max_cgpa=10.0,
                is_verified=True,
            )
        ],
        skills=["Python", "Machine Learning", "Pydantic", "SQL"],
    )


@pytest.fixture
def base_listing():
    return Listing(
        listing_id="opp_google_01",
        source_id="greenhouse",
        source_record_id="gh_101",
        canonical_url="https://careers.google.com/jobs/results/101",
        title="Software Engineering Intern - Machine Learning",
        organization="Google",
        description="Join the ML research team working on large models.",
        locations=["Bangalore"],
        work_mode=WorkMode.HYBRID,
        deadline="2026-12-31",
        min_gpa=7.5,
        eligible_branches=["Computer Science", "Information Technology", "Data Science"],
        eligible_years=[2026, 2027],
        required_skills=["Python", "Machine Learning"],
    )


def test_eligible_candidate(base_listing, base_profile):
    """Candidate satisfies all hard constraints."""
    ref_date = date(2026, 11, 15)
    result = check_eligibility(base_listing, base_profile, current_date=ref_date)
    assert result.verdict == EligibilityVerdict.ELIGIBLE
    assert len(result.disqualifiers) == 0
    assert any("Application deadline is valid" in r for r in result.reasons)
    assert any("Graduation year satisfied" in r for r in result.reasons)


def test_expired_deadline_disqualifies(base_listing, base_profile):
    """Listing deadline expired yesterday -> strictly INELIGIBLE."""
    base_listing.deadline = "2026-11-14"
    ref_date = date(2026, 11, 15)
    result = check_eligibility(base_listing, base_profile, current_date=ref_date)
    assert result.verdict == EligibilityVerdict.INELIGIBLE
    assert any("expired" in d.lower() for d in result.disqualifiers)


def test_graduation_year_mismatch(base_listing, base_profile):
    """Role requires 2024 or 2025 graduates, student is 2026 -> INELIGIBLE."""
    base_listing.eligible_years = [2024, 2025]
    ref_date = date(2026, 11, 15)
    result = check_eligibility(base_listing, base_profile, current_date=ref_date)
    assert result.verdict == EligibilityVerdict.INELIGIBLE
    assert any("Graduation year mismatch" in d for d in result.disqualifiers)


def test_branch_mismatch(base_listing, base_profile):
    """Role requires Mechanical or Civil engineering -> INELIGIBLE."""
    base_listing.eligible_branches = ["Mechanical Engineering", "Civil Engineering"]
    ref_date = date(2026, 11, 15)
    result = check_eligibility(base_listing, base_profile, current_date=ref_date)
    assert result.verdict == EligibilityVerdict.INELIGIBLE
    assert any("Eligible branch requirement not met" in d for d in result.disqualifiers)


def test_min_gpa_failure(base_listing, base_profile):
    """Role requires 9.0 CGPA, student has 8.8 -> INELIGIBLE."""
    base_listing.min_gpa = 9.0
    ref_date = date(2026, 11, 15)
    result = check_eligibility(base_listing, base_profile, current_date=ref_date)
    assert result.verdict == EligibilityVerdict.INELIGIBLE
    assert any("Minimum CGPA not met" in d for d in result.disqualifiers)


def test_unknown_when_profile_gpa_missing(base_listing, base_profile):
    """Role specifies min GPA 8.0, but candidate profile does not specify CGPA -> UNKNOWN."""
    base_profile.education[0].cgpa = None
    base_listing.min_gpa = 8.0
    ref_date = date(2026, 11, 15)
    result = check_eligibility(base_listing, base_profile, current_date=ref_date)
    assert result.verdict == EligibilityVerdict.UNKNOWN
    assert any("Candidate CGPA/GPA is unspecified" in u for u in result.unknown_factors)


def test_hard_work_mode_constraint(base_listing, base_profile):
    """Student has hard preference for Remote, but listing is On-Site -> INELIGIBLE."""
    base_listing.work_mode = WorkMode.ON_SITE
    preference = Preference(
        profile_id="prof_faizan",
        work_modes=[WorkMode.REMOTE],
        constraints={"hard_work_mode": True},
    )
    ref_date = date(2026, 11, 15)
    result = check_eligibility(base_listing, base_profile, preference=preference, current_date=ref_date)
    assert result.verdict == EligibilityVerdict.INELIGIBLE
    assert any("Work mode conflict" in d for d in result.disqualifiers)
