"""
Greenhouse Job Board API Connector
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 2.1, Section 6.1, Table 5, Table 8

Uses Greenhouse's documented, unauthenticated public read endpoints:
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

Guarantees:
- Read-only GET operations.
- Application submission endpoints (POST) are strictly omitted.
- HTML content is safely stripped to plain text.
- Outputs strongly typed Pydantic Listing objects with full provenance.
"""

import re
import html
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from tools.schemas import Listing, WorkMode


def strip_html_tags(html_text: str) -> str:
    """Safely converts HTML job description into normalized plain text."""
    if not html_text:
        return ""
    # Unescape HTML entities
    unescaped = html.unescape(html_text)
    # Remove script and style elements
    clean = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", unescaped, flags=re.DOTALL | re.IGNORECASE)
    # Convert <br>, <p>, <li> to newlines
    clean = re.sub(r"<(br|p|/p|li)[^>]*>", "\n", clean, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    clean = re.sub(r"<[^>]+>", " ", clean)
    # Normalize excessive whitespace
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    return "\n".join(lines)


def detect_work_mode(text: str, location: str) -> WorkMode:
    combined = f"{text} {location}".lower()
    if "remote" in combined:
        return WorkMode.REMOTE
    if "hybrid" in combined:
        return WorkMode.HYBRID
    if "on-site" in combined or "onsite" in combined or "in-office" in combined:
        return WorkMode.ON_SITE
    return WorkMode.UNKNOWN


class GreenhouseConnector:
    """
    Authorized read connector for employer Greenhouse job boards.
    """
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_board_jobs(
        self,
        board_token: str,
        organization_name: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ) -> List[Listing]:
        """
        Fetches published job postings from an employer's Greenhouse board.
        """
        url = f"{self.BASE_URL}/{board_token}/jobs?content=true"
        org = organization_name or board_token.capitalize()
        
        try:
            if client:
                response = client.get(url, timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as http_client:
                    response = http_client.get(url)
            
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            # Safe network failure handling
            return []

        jobs_data = data.get("jobs", [])
        listings: List[Listing] = []

        for job in jobs_data:
            job_id = str(job.get("id", ""))
            title = job.get("title", "").strip()
            if not title:
                continue

            raw_content = job.get("content", "")
            plain_desc = strip_html_tags(raw_content)

            loc_name = ""
            if isinstance(job.get("location"), dict):
                loc_name = job["location"].get("name", "")
            elif isinstance(job.get("location"), str):
                loc_name = job.get("location", "")

            locations = [loc_name.strip()] if loc_name.strip() else []
            work_mode = detect_work_mode(plain_desc, loc_name)
            canonical_url = job.get("absolute_url") or f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}"

            # Content hash for deduplication
            content_hash = hashlib.sha256(f"{title}|{org}|{plain_desc[:200]}".encode("utf-8")).hexdigest()

            listing = Listing(
                listing_id=f"gh_{board_token}_{job_id}",
                source_id="greenhouse",
                source_record_id=job_id,
                canonical_url=canonical_url,
                title=title,
                organization=org,
                description=plain_desc,
                locations=locations,
                work_mode=work_mode,
                deadline=None,
                stipend=None,
                currency="INR",
                retrieved_at=datetime.utcnow(),
                content_hash=content_hash,
            )
            listings.append(listing)

        return listings
