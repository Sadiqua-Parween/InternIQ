"""
Unit Tests for Application Tracker and SQLite Persistence Module
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 7, Table 6, FR-10, FR-11
"""

import pytest
from datetime import datetime
from tools.tracker import ApplicationTracker
from tools.schemas import (
    TrackerEvent,
    TrackerEventType,
    Profile,
    Listing,
    ApplicationDraft,
    Education,
    Project,
    EvidenceFact,
    ClaimAudit,
    ClaimStatus,
    WorkMode,
)


@pytest.fixture
def tracker_db(tmp_path):
    db_file = str(tmp_path / "test_interniq.db")
    return ApplicationTracker(db_path=db_file)


def test_tracker_event_confirmation_gate(tracker_db):
    """FR-11: Pauses before consequential state change; unconfirmed events raise ValueError."""
    unconfirmed = TrackerEvent(
        event_id="evt_01",
        opportunity_id="opp_1",
        event_type=TrackerEventType.APPLIED,
        event_time=datetime.utcnow(),
        user_confirmed=False,
        idempotency_key="idemp_01",
    )
    with pytest.raises(ValueError, match="requires explicit student confirmation"):
        tracker_db.record_event(unconfirmed)

    confirmed = TrackerEvent(
        event_id="evt_01",
        opportunity_id="opp_1",
        event_type=TrackerEventType.APPLIED,
        event_time=datetime.utcnow(),
        user_confirmed=True,
        idempotency_key="idemp_01",
        notes="Applied manually on company portal",
    )
    assert tracker_db.record_event(confirmed)

    events = tracker_db.get_events(opportunity_id="opp_1")
    assert len(events) == 1
    assert events[0]["event_type"] == "applied"
    assert events[0]["notes"] == "Applied manually on company portal"


def test_profile_persistence(tracker_db):
    """FR-02 & Table 6: Profile saving and retrieval."""
    profile = Profile(
        profile_id="prof_test_01",
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
        skills=["Python", "Machine Learning"],
        projects=[
            Project(
                title="InternIQ",
                description="Agentic internship assistant",
                skills_used=["Python"],
            )
        ],
        confirmed_facts=[
            EvidenceFact(
                fact_id="fact_1",
                fact_type="skill",
                text="Proficient in Python",
                source_doc="resume.txt",
                confidence=1.0,
                confirmed_by_user=True,
            )
        ],
    )

    assert tracker_db.save_profile(profile)
    retrieved = tracker_db.get_profile("prof_test_01")
    assert retrieved is not None
    assert retrieved.full_name == "Sadiqua Parween"
    assert retrieved.email == "falaksadiqua786@gmail.com"
    assert len(retrieved.education) == 1
    assert retrieved.education[0].graduation_year == 2026
    assert len(retrieved.confirmed_facts) == 1
    assert retrieved.confirmed_facts[0].fact_id == "fact_1"


def test_opportunity_snapshot_persistence(tracker_db):
    """Table 6: Opportunity snapshot caching and query."""
    listing = Listing(
        listing_id="opp_test_01",
        source_id="greenhouse",
        source_record_id="gh_999",
        canonical_url="https://boards.greenhouse.io/corp/jobs/999",
        title="ML Engineer Intern",
        organization="AI Corp",
        description="Deep learning research.",
        work_mode=WorkMode.REMOTE,
        locations=["Bengaluru"],
        eligible_years=[2026],
        required_skills=["Python", "PyTorch"],
    )

    assert tracker_db.save_opportunity(listing)
    retrieved = tracker_db.get_opportunity("opp_test_01")
    assert retrieved is not None
    assert retrieved.title == "ML Engineer Intern"
    assert retrieved.organization == "AI Corp"
    assert retrieved.work_mode == WorkMode.REMOTE

    all_opps = tracker_db.list_opportunities(source_id="greenhouse")
    assert len(all_opps) == 1


def test_draft_persistence(tracker_db):
    """Table 6: Application draft saving and retrieval."""
    draft = ApplicationDraft(
        draft_id="draft_01",
        opportunity_id="opp_test_01",
        profile_id="prof_01",
        version=1,
        tailored_resume_bullets=["Developed ML model using PyTorch."],
        cover_letter="Dear Hiring Team, ...",
        claims=[
            ClaimAudit(
                claim_id="c1",
                claim_text="Experienced in PyTorch",
                claim_type="skill",
                status=ClaimStatus.SUPPORTED,
                supporting_fact_ids=["fact_pytorch"],
            )
        ],
        is_fully_grounded=True,
    )

    assert tracker_db.save_draft(draft)
    retrieved = tracker_db.get_draft("draft_01")
    assert retrieved is not None
    assert retrieved.tailored_resume_bullets == ["Developed ML model using PyTorch."]
    assert retrieved.is_fully_grounded is True


def test_feedback_and_export(tracker_db):
    fb_id = tracker_db.save_feedback("opp_test_01", "good_match", "Aligned with my skills")
    assert fb_id.startswith("fb_")

    data = tracker_db.export_all_user_data()
    assert "exported_at" in data
    assert len(data["feedback"]) == 1
    assert data["feedback"][0]["label"] == "good_match"


def test_dpdp_full_deletion(tracker_db):
    """Section 7.2 & Table 10: Complete user data deletion."""
    event = TrackerEvent(
        event_id="evt_01",
        opportunity_id="opp_1",
        event_type=TrackerEventType.SAVED,
        event_time=datetime.utcnow(),
        user_confirmed=True,
        idempotency_key="idemp_01",
    )
    tracker_db.record_event(event)
    tracker_db.save_feedback("opp_1", "saved")

    deleted = tracker_db.delete_all_user_data()
    assert deleted == 1
    assert len(tracker_db.get_events()) == 0
    exported = tracker_db.export_all_user_data()
    assert len(exported["feedback"]) == 0
    assert len(exported["audit_log"]) == 0
