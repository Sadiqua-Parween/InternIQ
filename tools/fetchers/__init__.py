"""
Data Ingestion and Authorized Source Connectors
Owner: Sadiqua Parween (Team HumanBot)
Status: Interface Stubs & Controlled Offline Fixture Fetcher

Implements tool contract for `fetch_opportunities` and `import_csv_or_url`.
Strict read-only GET; no scraping unauthorized endpoints, no CAPTCHA bypass.
"""

from typing import List, Optional
import csv
import io
import hashlib
from datetime import datetime
from tools.schemas import Listing, WorkMode


def normalize_dedupe(raw_listings: List[Listing]) -> List[Listing]:
    """
    Deduplicates listings across sources using content hash, canonical URLs,
    and source record IDs. Preserves provenance links.
    """
    seen_hashes = set()
    seen_urls = set()
    deduped = []
    
    for item in raw_listings:
        # Compute content hash if empty
        if not item.content_hash:
            normalized_text = f"{item.title.strip().lower()}|{item.organization.strip().lower()}|{item.description[:200].strip().lower()}"
            item.content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
            
        canonical = item.canonical_url.strip().lower()
        if item.content_hash in seen_hashes or (canonical and canonical in seen_urls):
            continue
            
        seen_hashes.add(item.content_hash)
        if canonical:
            seen_urls.add(canonical)
        deduped.append(item)
        
    return deduped


def import_csv(file_content: str, source_id: str = "manual_csv") -> List[Listing]:
    """
    Parses a CSV stream of job opportunities into validated Listing objects.
    """
    reader = csv.DictReader(io.StringIO(file_content))
    listings = []
    
    for idx, row in enumerate(reader):
        title = row.get("title", "").strip()
        org = row.get("organization", row.get("company", "")).strip()
        desc = row.get("description", "").strip()
        url = row.get("canonical_url", row.get("url", f"https://example.com/job/{idx}")).strip()
        
        if not title:
            continue
            
        req_skills_raw = row.get("required_skills", "")
        req_skills = [s.strip() for s in req_skills_raw.split(",") if s.strip()]
        
        pref_skills_raw = row.get("preferred_skills", "")
        pref_skills = [s.strip() for s in pref_skills_raw.split(",") if s.strip()]
        
        locations_raw = row.get("locations", row.get("location", ""))
        locations = [l.strip() for l in locations_raw.split(",") if l.strip()]
        
        # Parse years
        years_raw = row.get("eligible_years", "")
        eligible_years = []
        if years_raw:
            for y in years_raw.split(","):
                try:
                    eligible_years.append(int(y.strip()))
                except ValueError:
                    pass
                    
        # Parse GPA
        min_gpa = None
        if row.get("min_gpa"):
            try:
                min_gpa = float(row.get("min_gpa"))
            except ValueError:
                pass
                
        # Parse stipend
        stipend = None
        if row.get("stipend"):
            try:
                stipend = float(row.get("stipend"))
            except ValueError:
                pass

        work_mode_str = row.get("work_mode", "unknown").lower().replace("-", "_")
        try:
            work_mode = WorkMode(work_mode_str)
        except ValueError:
            work_mode = WorkMode.UNKNOWN

        content_hash = hashlib.sha256(f"{title}|{org}|{desc[:200]}".encode("utf-8")).hexdigest()

        listing = Listing(
            listing_id=row.get("listing_id", f"{source_id}_{idx}_{content_hash[:8]}"),
            source_id=source_id,
            source_record_id=row.get("source_record_id", str(idx)),
            canonical_url=url,
            title=title,
            organization=org,
            description=desc,
            locations=locations,
            work_mode=work_mode,
            start_date=row.get("start_date"),
            deadline=row.get("deadline"),
            eligibility_text=row.get("eligibility_text"),
            min_gpa=min_gpa,
            eligible_branches=[b.strip() for b in row.get("eligible_branches", "").split(",") if b.strip()],
            eligible_years=eligible_years,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            stipend=stipend,
            currency=row.get("currency", "INR"),
            retrieved_at=datetime.utcnow(),
            content_hash=content_hash,
        )
        listings.append(listing)
        
    return normalize_dedupe(listings)
