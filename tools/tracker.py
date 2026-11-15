"""
Application Tracker and SQLite Persistence Module
Owner: Sadiqua Parween (Team HumanBot)
Status: Local SQLite Persistence Implementation

Implements local storage for profiles, listings, drafts, and application tracking events.
Enforces local data minimization, user-confirmed tracker events, and GDPR/DPDP-compliant deletion.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from tools.schemas import TrackerEvent, TrackerEventType


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

    def record_event(self, event: TrackerEvent) -> bool:
        """
        Records an application lifecycle event idempotently with user confirmation check.
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
                    ("RECORD_EVENT", "student", datetime.utcnow().isoformat(), json.dumps({"event_id": event.event_id, "type": str(event.event_type)})),
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

    def delete_all_user_data(self) -> int:
        """
        DPDP compliance: Full local data erasure.
        """
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM tracker_events")
            deleted = cur.rowcount
            conn.execute("DELETE FROM audit_log")
            conn.commit()
            return deleted
