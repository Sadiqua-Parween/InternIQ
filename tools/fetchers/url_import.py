"""
User-Supplied URL Opportunity Importer
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 6.1, Section 6.5, Table 5, Table 10

Safely fetches an internship opportunity from a user-provided public URL.
Strict SSRF protection:
- Validates URL schema, blocks private/metadata IPs.
- Bounds response payload size (max 2MB).
- Strips scripts and executes zero JavaScript.
"""

import re
import hashlib
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse
import httpx
from tools.schemas import Listing, WorkMode
from tools.fetchers.url_safety import validate_safe_url
from tools.fetchers.greenhouse import strip_html_tags, detect_work_mode


def import_url_opportunity(
    url: str,
    allow_local_fixtures: bool = False,
    timeout: float = 8.0,
    client: Optional[httpx.Client] = None,
) -> Tuple[Optional[Listing], Optional[str]]:
    """
    Safely retrieves and parses an opportunity from a validated public URL.
    
    Returns:
        (Listing, None) on success, or (None, error_message) on failure.
    """
    is_safe, error = validate_safe_url(url, allow_local_fixtures=allow_local_fixtures)
    if not is_safe:
        return None, f"URL rejected by security controls: {error}"

    headers = {
        "User-Agent": "InternIQ-Assistant/1.0 (Educational Academic Project; contact@interniq.local)"
    }

    try:
        if client:
            response = client.get(url, headers=headers, timeout=timeout, follow_redirects=False)
        else:
            with httpx.Client(timeout=timeout, follow_redirects=False) as http_client:
                response = http_client.get(url, headers=headers)

        if response.status_code in (301, 302, 303, 307, 308):
            redirect_url = response.headers.get("Location")
            if not redirect_url:
                return None, "Redirect without Location header."
            # Re-validate redirect destination against SSRF rules!
            is_redir_safe, redir_err = validate_safe_url(redirect_url, allow_local_fixtures=allow_local_fixtures)
            if not is_redir_safe:
                return None, f"Redirect destination rejected: {redir_err}"
            # Fetch redirect target
            if client:
                response = client.get(redirect_url, headers=headers, timeout=timeout)
            else:
                with httpx.Client(timeout=timeout) as http_client:
                    response = http_client.get(redirect_url, headers=headers)

        response.raise_for_status()

        # Enforce max content size limit (2 MB)
        if len(response.content) > 2 * 1024 * 1024:
            return None, "Listing page content exceeds maximum allowed size (2MB)."

        html_content = response.text
    except Exception as e:
        return None, f"Failed to fetch listing from URL: {str(e)}"

    # Parse basic metadata from HTML
    parsed_url = urlparse(url)
    domain = parsed_url.hostname or "external_source"
    
    # Extract Title tag
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
    title = strip_html_tags(title_match.group(1)) if title_match else "Internship Opportunity"
    # Clean up common title suffixes like " - Careers", " | Company"
    title_cleaned = re.split(r"[-|•–]", title)[0].strip() or title.strip()

    # Extract Organization from domain or open graph
    og_site = re.search(r'<meta\s+property=["\']og:site_name["\']\s+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    org = og_site.group(1).strip() if og_site else domain.replace("www.", "").split(".")[0].capitalize()

    plain_desc = strip_html_tags(html_content)
    # Clip description to reasonable size
    plain_desc_trimmed = plain_desc[:10000]

    work_mode = detect_work_mode(plain_desc_trimmed, "")
    content_hash = hashlib.sha256(f"{title_cleaned}|{org}|{plain_desc_trimmed[:200]}".encode("utf-8")).hexdigest()

    listing = Listing(
        listing_id=f"url_{content_hash[:10]}",
        source_id="user_url",
        source_record_id=content_hash[:8],
        canonical_url=url,
        title=title_cleaned,
        organization=org,
        description=plain_desc_trimmed,
        locations=[],
        work_mode=work_mode,
        deadline=None,
        stipend=None,
        currency="INR",
        retrieved_at=datetime.utcnow(),
        content_hash=content_hash,
    )

    return listing, None
