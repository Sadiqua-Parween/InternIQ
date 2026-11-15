"""
Unit Tests for Scam-Signal Detection Engine
Owner: Mohd Faizan Khan (Team HumanBot)
"""

import pytest
from tools.schemas import Listing, WorkMode, RiskSeverity
from tools.scam_check import check_scam_signals


def test_clean_listing_no_flags():
    """Legitimate corporate posting produces zero risk flags."""
    listing = Listing(
        listing_id="clean_01",
        source_id="greenhouse",
        source_record_id="gh_999",
        canonical_url="https://boards.greenhouse.io/stripe/jobs/12345",
        title="Backend Software Engineering Intern",
        organization="Stripe",
        description="Build developer-first financial infrastructure. Work with Python, Go, and distributed systems.",
        locations=["Bangalore"],
        work_mode=WorkMode.HYBRID,
        required_skills=["Python", "Distributed Systems"],
    )
    result = check_scam_signals(listing)
    assert not result.is_suspicious
    assert len(result.flags) == 0
    assert result.highest_severity is None
    assert "No risk signals detected" in result.verdict_summary


def test_fee_request_flagged():
    """Posting requiring application fee or training deposit is flagged HIGH risk."""
    listing = Listing(
        listing_id="scam_fee_01",
        source_id="manual_csv",
        source_record_id="csv_1",
        canonical_url="https://example.com/apply",
        title="Web Developer Trainee",
        organization="TechCorp Solutions",
        description="Join our fast-track internship. Selected candidates must pay Rs 2500 registration fee for orientation kit.",
        locations=["Remote"],
        work_mode=WorkMode.REMOTE,
    )
    result = check_scam_signals(listing)
    assert result.is_suspicious
    assert result.highest_severity == RiskSeverity.HIGH
    assert any(f.code == "FEE_REQUEST" for f in result.flags)
    fee_flag = next(f for f in result.flags if f.code == "FEE_REQUEST")
    assert "Possible risk signal" in fee_flag.explanation
    assert "fraud" not in fee_flag.explanation.lower()  # Non-accusatory language


def test_free_email_domain_flagged():
    """Corporate firm using public @gmail address is flagged MEDIUM risk."""
    listing = Listing(
        listing_id="scam_email_01",
        source_id="manual_csv",
        source_record_id="csv_2",
        canonical_url="https://example.com/job",
        title="Data Analyst Intern",
        organization="Amazon Development Centre",
        description="Analyze retail metrics. Interested students send resume directly to hr_amazon_recruit@gmail.com immediately.",
        locations=["Hyderabad"],
        work_mode=WorkMode.ON_SITE,
    )
    result = check_scam_signals(listing)
    assert any(f.code == "UNVERIFIED_EMAIL_DOMAIN" for f in result.flags)
    email_flag = next(f for f in result.flags if f.code == "UNVERIFIED_EMAIL_DOMAIN")
    assert "gmail.com" in email_flag.evidence_snippet


def test_implausible_urgency_flagged():
    """High-pressure instant hiring phrase is flagged."""
    listing = Listing(
        listing_id="scam_urgent_01",
        source_id="manual_csv",
        source_record_id="csv_3",
        canonical_url="https://example.com/job",
        title="Junior Python Intern",
        organization="FastTrack Media",
        description="Immediate hire without interview. Start earning today from home.",
        locations=["Remote"],
        work_mode=WorkMode.REMOTE,
    )
    result = check_scam_signals(listing)
    assert any(f.code == "IMPLAUSIBLE_URGENCY" for f in result.flags)


def test_sensitive_info_request_flagged():
    """Requesting bank account details or OTP upfront is flagged HIGH risk."""
    listing = Listing(
        listing_id="scam_sensitive_01",
        source_id="manual_csv",
        source_record_id="csv_4",
        canonical_url="https://example.com/job",
        title="Finance Intern",
        organization="Direct Capital",
        description="Verify your stipend account by providing bank account number and OTP during form submission.",
        locations=["Mumbai"],
        work_mode=WorkMode.ON_SITE,
    )
    result = check_scam_signals(listing)
    assert result.highest_severity == RiskSeverity.HIGH
    assert any(f.code == "SENSITIVE_INFO_REQUEST" for f in result.flags)


def test_domain_mismatch_flagged():
    """Official organization linking to google forms or free blog is flagged."""
    listing = Listing(
        listing_id="scam_domain_01",
        source_id="manual_csv",
        source_record_id="csv_5",
        canonical_url="https://forms.gle/xyz123fake",
        title="ML Engineer Intern",
        organization="Microsoft India",
        description="Apply for our premier AI research lab internship via the Google Form.",
        locations=["Bangalore"],
        work_mode=WorkMode.HYBRID,
    )
    result = check_scam_signals(listing)
    assert any(f.code == "DOMAIN_MISMATCH" for f in result.flags)
