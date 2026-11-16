"""
Lever Postings API Connector
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 2.1, Section 6.1, Table 5, Table 8

Uses Lever's documented, unauthenticated public read endpoints:
GET https://api.lever.co/v0/postings/{site}

Guarantees:
- Read-only GET operations.
- Application submission endpoints (POST) are strictly omitted.
- Normalizes work mode and plain-text descriptions.
- Outputs strongly typed Pydantic Listing objects with full provenance.
"""

import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from tools.schemas import Listing, WorkMode
from tools.fetchers.greenhouse import strip_html_tags, detect_work_mode


class LeverConnector:
    """
    Authorized read connector for employer Lever postings.
    """
    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_site_postings(
        self,
        site: str,
        organization_name: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ) -> List[Listing]:
        """
        Fetches published postings from an employer's Lever site.
        """
        url = f"{self.BASE_URL}/{site}?mode=json"
        org = organization_name or site.capitalize()

        try:
            if client:
                response = client.get(url, timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as http_client:
                    response = http_client.get(url)

            response.raise_for_status()
            postings_data = response.json()
        except Exception:
            return []

        if not isinstance(postings_data, list):
            return []

        listings: List[Listing] = []

        for posting in postings_data:
            posting_id = str(posting.get("id", ""))
            title = posting.get("text", "").strip()
            if not title:
                continue

            plain_desc = posting.get("descriptionPlain", "")
            if not plain_desc and posting.get("description"):
                plain_desc = strip_html_tags(posting["description"])

            categories = posting.get("categories", {})
            loc_name = categories.get("location", "") if isinstance(categories, dict) else ""
            locations = [loc_name.strip()] if loc_name.strip() else []

            commitment = categories.get("commitment", "") if isinstance(categories, dict) else ""
            work_mode = detect_work_mode(f"{plain_desc} {commitment}", loc_name)
            canonical_url = posting.get("hostedUrl") or f"https://jobs.lever.co/{site}/{posting_id}"

            content_hash = hashlib.sha256(f"{title}|{org}|{plain_desc[:200]}".encode("utf-8")).hexdigest()

            listing = Listing(
                listing_id=f"lever_{site}_{posting_id}",
                source_id="lever",
                source_record_id=posting_id,
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
