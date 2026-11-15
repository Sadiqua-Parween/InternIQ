"""
Application Packet Builder Module
Owner: Sadiqua Parween (Team HumanBot)
Status: Interface Stub

Prepares full application packet (tailored resume bullets, cover letter,
eligibility summary, company notes) for manual student review and copy-paste.
No automatic application submission.
"""

from typing import Dict, Any
from tools.schemas import Listing, Profile, ApplicationDraft


def build_application_packet(
    listing: Listing,
    profile: Profile,
    draft: ApplicationDraft,
) -> Dict[str, Any]:
    """
    Assembles a field-by-field packet ready for the student to review,
    copy into the employer portal, and manually submit.
    """
    return {
        "opportunity_id": listing.listing_id,
        "title": listing.title,
        "organization": listing.organization,
        "application_url": listing.canonical_url,
        "applicant_name": profile.full_name,
        "applicant_email": profile.email,
        "applicant_phone": profile.phone or "Not specified",
        "tailored_resume_bullets": draft.tailored_resume_bullets,
        "cover_letter": draft.cover_letter,
        "claims_audit_summary": {
            "is_fully_grounded": draft.is_fully_grounded,
            "total_claims": len(draft.claims),
            "unsupported_claims": draft.unsupported_claim_count,
        },
        "manual_submission_notice": (
            "NOTICE: Automatic application submission is disabled. "
            "Please review the materials above, click the canonical application URL, "
            "and submit manually in the employer portal."
        ),
    }
