"""
Application Tracker and SQLite Persistence Module
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 7, Table 6, FR-10, FR-11

Implements local storage for profiles, listings, drafts, and application tracking events.
Enforces local data minimization, user-confirmed tracker events, and GDPR/DPDP-compliant deletion.

Tables:
- tracker_events: Stage transitions (SAVED, SHORTLISTED, APPLIED, INTERVIEW, OFFER, REJECTED)
- profiles: Student profile facts & confirmed EvidenceFacts
- opportunities: Cached listing snapshots & provenance
- drafts: Grounded application drafts & claim audits
- feedback: Student ranking/match preference feedback
- audit_log: Verifiable security & data lifecycle audit trail
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from tools.schemas import (
    TrackerEvent,
    TrackerEventType,
    Profile,
    Listing,
    ApplicationDraft,
    WorkMode,
    Education,
    Project,
    EvidenceFact,
    ClaimAudit,
    ClaimStatus,
)


class ApplicationTracker:
    def __init__(self, db_path: str = "interniq.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            # 1. Tracker Events Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tracker_events (
                    event_id TEXT PRIMARY KEY,
                    opportunity_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    user_confirmed INTEGER NOT NULL,
                    idempotency_key TEXT UNIQUE NOT NULL,
                    notes TEXT
                )
            """)
            # 2. Student Profiles Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    profile_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    education_json TEXT NOT NULL,
                    skills_json TEXT NOT NULL,
                    projects_json TEXT NOT NULL,
                    confirmed_facts_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # 3. Opportunities Snapshot Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    opportunity_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_record_id TEXT NOT NULL,
                    canonical_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    description TEXT NOT NULL,
                    locations_json TEXT NOT NULL,
                    work_mode TEXT NOT NULL,
                    deadline TEXT,
                    eligibility_text TEXT,
                    min_gpa REAL,
                    eligible_branches_json TEXT NOT NULL,
                    eligible_years_json TEXT NOT NULL,
                    required_skills_json TEXT NOT NULL,
                    preferred_skills_json TEXT NOT NULL,
                    stipend REAL,
                    currency TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL
                )
            """)
            # 4. Application Drafts Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS drafts (
                    draft_id TEXT PRIMARY KEY,
                    opportunity_id TEXT NOT NULL,
                    profile_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    resume_bullets_json TEXT NOT NULL,
                    cover_letter TEXT NOT NULL,
                    claims_json TEXT NOT NULL,
                    is_fully_grounded INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            # 5. User Feedback Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id TEXT PRIMARY KEY,
                    opportunity_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            # 6. Audit Log Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT
                )
            """)
            conn.commit()

    # =========================================================================
    # Tracker Events (Human Approval Gate & Idempotency)
    # =========================================================================

    def record_event(self, event: TrackerEvent) -> bool:
        """
        Records an application lifecycle event idempotently with user confirmation check.
        Strictly enforces FR-11: Pauses before consequential state change.
        """
        if not event.user_confirmed:
            raise ValueError("Tracker event requires explicit student confirmation.")

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO tracker_events 
                    (event_id, opportunity_id, event_type, event_time, user_confirmed, idempotency_key, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(idempotency_key) DO UPDATE SET
                    event_type=excluded.event_type,
                    event_time=excluded.event_time,
                    notes=excluded.notes
                    """,
                    (
                        event.event_id,
                        event.opportunity_id,
                        event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                        event.event_time.isoformat(),
                        1 if event.user_confirmed else 0,
                        event.idempotency_key,
                        event.notes,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO audit_log (action, actor, timestamp, details)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        "RECORD_EVENT",
                        "student",
                        datetime.utcnow().isoformat(),
                        json.dumps({"event_id": event.event_id, "type": str(event.event_type), "opportunity_id": event.opportunity_id}),
                    ),
                )
                conn.commit()
                return True
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def get_events(self, opportunity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            if opportunity_id:
                cur = conn.execute(
                    "SELECT * FROM tracker_events WHERE opportunity_id = ? ORDER BY event_time DESC",
                    (opportunity_id,),
                )
            else:
                cur = conn.execute("SELECT * FROM tracker_events ORDER BY event_time DESC")
            return [dict(row) for row in cur.fetchall()]

    # =========================================================================
    # Profile Persistence
    # =========================================================================

    def save_profile(self, profile: Profile) -> bool:
        """Saves or updates candidate Profile."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO profiles
                (profile_id, full_name, email, phone, education_json, skills_json, projects_json, confirmed_facts_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id) DO UPDATE SET
                full_name=excluded.full_name,
                email=excluded.email,
                phone=excluded.phone,
                education_json=excluded.education_json,
                skills_json=excluded.skills_json,
                projects_json=excluded.projects_json,
                confirmed_facts_json=excluded.confirmed_facts_json,
                updated_at=excluded.updated_at
                """,
                (
                    profile.profile_id,
                    profile.full_name,
                    profile.email,
                    profile.phone,
                    json.dumps([e.model_dump() for e in profile.education]),
                    json.dumps(profile.skills),
                    json.dumps([p.model_dump() for p in profile.projects]),
                    json.dumps([f.model_dump() for f in profile.confirmed_facts]),
                    profile.updated_at.isoformat(),
                ),
            )
            conn.commit()
            return True

    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Retrieves candidate Profile by ID."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM profiles WHERE profile_id = ?", (profile_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Profile(
                profile_id=row["profile_id"],
                full_name=row["full_name"],
                email=row["email"],
                phone=row["phone"],
                education=[Education(**e) for e in json.loads(row["education_json"])],
                skills=json.loads(row["skills_json"]),
                projects=[Project(**p) for p in json.loads(row["projects_json"])],
                confirmed_facts=[EvidenceFact(**f) for f in json.loads(row["confirmed_facts_json"])],
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    # =========================================================================
    # Opportunity Snapshot Persistence
    # =========================================================================

    def save_opportunity(self, listing: Listing) -> bool:
        """Saves or updates an opportunity listing snapshot."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO opportunities
                (opportunity_id, source_id, source_record_id, canonical_url, title, organization, description,
                 locations_json, work_mode, deadline, eligibility_text, min_gpa, eligible_branches_json,
                 eligible_years_json, required_skills_json, preferred_skills_json, stipend, currency, retrieved_at, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(opportunity_id) DO UPDATE SET
                title=excluded.title,
                organization=excluded.organization,
                description=excluded.description,
                deadline=excluded.deadline,
                work_mode=excluded.work_mode,
                stipend=excluded.stipend,
                retrieved_at=excluded.retrieved_at
                """,
                (
                    listing.listing_id,
                    listing.source_id,
                    listing.source_record_id,
                    listing.canonical_url,
                    listing.title,
                    listing.organization,
                    listing.description,
                    json.dumps(listing.locations),
                    listing.work_mode.value if hasattr(listing.work_mode, "value") else str(listing.work_mode),
                    listing.deadline,
                    listing.eligibility_text,
                    listing.min_gpa,
                    json.dumps(listing.eligible_branches),
                    json.dumps(listing.eligible_years),
                    json.dumps(listing.required_skills),
                    json.dumps(listing.preferred_skills),
                    listing.stipend,
                    listing.currency,
                    listing.retrieved_at.isoformat(),
                    listing.content_hash,
                ),
            )
            conn.commit()
            return True

    def get_opportunity(self, opportunity_id: str) -> Optional[Listing]:
        """Retrieves cached Listing snapshot by ID."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM opportunities WHERE opportunity_id = ?", (opportunity_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_listing(row)

    def list_opportunities(self, source_id: Optional[str] = None) -> List[Listing]:
        """Lists cached opportunities, optionally filtered by source."""
        with self._get_connection() as conn:
            if source_id:
                cur = conn.execute("SELECT * FROM opportunities WHERE source_id = ? ORDER BY retrieved_at DESC", (source_id,))
            else:
                cur = conn.execute("SELECT * FROM opportunities ORDER BY retrieved_at DESC")
            return [self._row_to_listing(row) for row in cur.fetchall()]

    def _row_to_listing(self, row: sqlite3.Row) -> Listing:
        return Listing(
            listing_id=row["opportunity_id"],
            source_id=row["source_id"],
            source_record_id=row["source_record_id"],
            canonical_url=row["canonical_url"],
            title=row["title"],
            organization=row["organization"],
            description=row["description"],
            locations=json.loads(row["locations_json"]),
            work_mode=WorkMode(row["work_mode"]),
            deadline=row["deadline"],
            eligibility_text=row["eligibility_text"],
            min_gpa=row["min_gpa"],
            eligible_branches=json.loads(row["eligible_branches_json"]),
            eligible_years=json.loads(row["eligible_years_json"]),
            required_skills=json.loads(row["required_skills_json"]),
            preferred_skills=json.loads(row["preferred_skills_json"]),
            stipend=row["stipend"],
            currency=row["currency"],
            retrieved_at=datetime.fromisoformat(row["retrieved_at"]),
            content_hash=row["content_hash"],
        )

    # =========================================================================
    # Application Draft Persistence
    # =========================================================================

    def save_draft(self, draft: ApplicationDraft) -> bool:
        """Saves generated and claim-verified application draft."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO drafts
                (draft_id, opportunity_id, profile_id, version, resume_bullets_json, cover_letter, claims_json, is_fully_grounded, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(draft_id) DO UPDATE SET
                resume_bullets_json=excluded.resume_bullets_json,
                cover_letter=excluded.cover_letter,
                claims_json=excluded.claims_json,
                is_fully_grounded=excluded.is_fully_grounded
                """,
                (
                    draft.draft_id,
                    draft.opportunity_id,
                    draft.profile_id,
                    draft.version,
                    json.dumps(draft.tailored_resume_bullets),
                    draft.cover_letter,
                    json.dumps([c.model_dump() for c in draft.claims]),
                    1 if draft.is_fully_grounded else 0,
                    draft.created_at.isoformat(),
                ),
            )
            conn.commit()
            return True

    def get_draft(self, draft_id: str) -> Optional[ApplicationDraft]:
        """Retrieves draft by ID."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM drafts WHERE draft_id = ?", (draft_id,))
            row = cur.fetchone()
            if not row:
                return None
            return ApplicationDraft(
                draft_id=row["draft_id"],
                opportunity_id=row["opportunity_id"],
                profile_id=row["profile_id"],
                version=int(row["version"]),
                tailored_resume_bullets=json.loads(row["resume_bullets_json"]),
                cover_letter=row["cover_letter"],
                claims=[ClaimAudit(**c) for c in json.loads(row["claims_json"])],
                is_fully_grounded=bool(row["is_fully_grounded"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    # =========================================================================
    # Feedback & User Control
    # =========================================================================

    def save_feedback(self, opportunity_id: str, label: str, reason: Optional[str] = None) -> str:
        """Stores candidate ranking feedback (e.g. good_match, irrelevant)."""
        fb_id = f"fb_{uuid.uuid4().hex[:8]}"
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO feedback (feedback_id, opportunity_id, label, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (fb_id, opportunity_id, label, reason, datetime.utcnow().isoformat()),
            )
            conn.commit()
            return fb_id

    # =========================================================================
    # DPDP / GDPR Deletion & Data Portability
    # =========================================================================

    def delete_all_user_data(self) -> int:
        """
        DPDP compliance: Full local data erasure.
        Deletes all profiles, opportunities, drafts, tracker events, feedback, and audit log.
        Returns total count of erased tracker events (preserving backward-compatible return value).
        """
        with self._get_connection() as conn:
            cur_events = conn.execute("DELETE FROM tracker_events")
            deleted_events_count = cur_events.rowcount
            conn.execute("DELETE FROM profiles")
            conn.execute("DELETE FROM opportunities")
            conn.execute("DELETE FROM drafts")
            conn.execute("DELETE FROM feedback")
            conn.execute("DELETE FROM audit_log")
            conn.commit()
            return deleted_events_count

    def export_all_user_data(self) -> Dict[str, Any]:
        """
        Data portability: Exports all local records as a structured JSON-serializable dictionary.
        """
        with self._get_connection() as conn:
            events = [dict(r) for r in conn.execute("SELECT * FROM tracker_events").fetchall()]
            profiles = [dict(r) for r in conn.execute("SELECT * FROM profiles").fetchall()]
            opportunities = [dict(r) for r in conn.execute("SELECT * FROM opportunities").fetchall()]
            drafts = [dict(r) for r in conn.execute("SELECT * FROM drafts").fetchall()]
            feedback = [dict(r) for r in conn.execute("SELECT * FROM feedback").fetchall()]
            audit = [dict(r) for r in conn.execute("SELECT * FROM audit_log").fetchall()]

            return {
                "exported_at": datetime.utcnow().isoformat(),
                "tracker_events": events,
                "profiles": profiles,
                "opportunities": opportunities,
                "drafts": drafts,
                "feedback": feedback,
                "audit_log": audit,
            }
