"""
Application Packet Builder Module
Owner: Sadiqua Parween (Team HumanBot)
Specification: Technical Report Section 3.1, FR-09, Section 4.2

Prepares full application packet (tailored resume bullets, cover letter,
eligibility summary, company notes) for manual student review and copy-paste.

Guarantees:
- Strict Human-in-the-Loop policy: automatic application submission is disabled.
- Outputs structured reviewable packet dictionary.
- Provides multi-format export functions (Markdown, JSON, Plaintext) for clipboard/export.
"""

import json
from typing import Dict, Any, Optional
from tools.schemas import Listing, Profile, ApplicationDraft, ScoreBreakdown


def build_application_packet(
    listing: Listing,
    profile: Profile,
    draft: ApplicationDraft,
    score_breakdown: Optional[ScoreBreakdown] = None,
) -> Dict[str, Any]:
    """
    Assembles a field-by-field packet ready for the student to review,
    copy into the employer portal, and manually submit.
    """
    packet = {
        "opportunity_id": listing.listing_id,
        "title": listing.title,
        "organization": listing.organization,
        "canonical_application_url": listing.canonical_url,
        "deadline": listing.deadline or "Not specified",
        "work_mode": listing.work_mode.value if hasattr(listing.work_mode, "value") else str(listing.work_mode),
        "locations": listing.locations,
        "stipend": f"{listing.stipend} {listing.currency}" if listing.stipend else "Not disclosed",
        
        # Applicant Information
        "applicant": {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone or "Not specified",
            "education": [
                {
                    "degree": e.degree,
                    "institution": e.institution,
                    "graduation_year": e.graduation_year,
                    "cgpa": e.cgpa,
                }
                for e in profile.education
            ],
            "skills": profile.skills,
        },
        
        # Generated Application Materials
        "tailored_resume_bullets": draft.tailored_resume_bullets,
        "cover_letter": draft.cover_letter,
        
        # Claim-Level Grounding Audit Summary
        "claims_audit_summary": {
            "is_fully_grounded": draft.is_fully_grounded,
            "total_claims": len(draft.claims),
            "unsupported_claims": draft.unsupported_claim_count,
            "audited_claims": [
                {
                    "claim_id": c.claim_id,
                    "claim_text": c.claim_text,
                    "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                    "supporting_facts": c.supporting_fact_ids,
                }
                for c in draft.claims
            ],
        },
        
        # Score Breakdown (if available)
        "match_score": {
            "total_score": round(score_breakdown.total_score, 4) if score_breakdown and score_breakdown.total_score is not None else None,
            "factor_scores": score_breakdown.factor_scores if score_breakdown else {},
            "missing_skills": score_breakdown.missing_skills if score_breakdown else [],
        } if score_breakdown else None,
        
        # Mandatory Safety & Human Control Notice
        "human_control_notice": (
            "NOTICE: Automatic application submission is disabled by design. "
            "Please review the materials above, click the canonical application URL, "
            "and submit manually in the employer's official portal."
        ),
    }

    return packet


def export_packet_markdown(packet: Dict[str, Any]) -> str:
    """
    Renders an application packet as clean, human-readable Markdown.
    """
    lines = []
    lines.append(f"# Application Packet: {packet['title']} at {packet['organization']}")
    lines.append("")
    lines.append(f"> **Application URL:** [{packet['canonical_application_url']}]({packet['canonical_application_url']})  ")
    lines.append(f"> **Deadline:** {packet['deadline']} | **Work Mode:** {packet['work_mode']} | **Stipend:** {packet['stipend']}")
    lines.append("")
    lines.append("---")
    lines.append("## 👤 Applicant Profile")
    applicant = packet.get("applicant", {})
    lines.append(f"- **Name:** {applicant.get('full_name')}")
    lines.append(f"- **Email:** {applicant.get('email')} | **Phone:** {applicant.get('phone')}")
    if applicant.get("education"):
        edu = applicant["education"][0]
        lines.append(f"- **Education:** {edu.get('degree')} from {edu.get('institution')} (Graduation: {edu.get('graduation_year')}, CGPA: {edu.get('cgpa')})")
    lines.append(f"- **Key Skills:** {', '.join(applicant.get('skills', []))}")
    lines.append("")
    lines.append("---")
    lines.append("## 📝 Tailored Resume Bullets")
    for bullet in packet.get("tailored_resume_bullets", []):
        lines.append(f"* {bullet}")
    lines.append("")
    lines.append("---")
    lines.append("## ✉️ Tailored Cover Letter")
    lines.append(packet.get("cover_letter", ""))
    lines.append("")
    lines.append("---")
    lines.append("## 🛡️ Grounding & Claim Audit")
    audit = packet.get("claims_audit_summary", {})
    lines.append(f"- **Fully Grounded:** {'✅ Yes' if audit.get('is_fully_grounded') else '❌ No'}")
    lines.append(f"- **Total Audited Claims:** {audit.get('total_claims')} | **Unsupported Claims:** {audit.get('unsupported_claims')}")
    lines.append("")
    lines.append("---")
    lines.append(f"> ⚠️ **{packet.get('human_control_notice')}**")
    lines.append("")
    return "\n".join(lines)


def export_packet_json(packet: Dict[str, Any]) -> str:
    """Serializes packet dictionary to formatted JSON."""
    return json.dumps(packet, indent=2, default=str)


def export_packet_text(packet: Dict[str, Any]) -> str:
    """Serializes packet to simple plain text suitable for direct copy-paste."""
    out = []
    out.append(f"INTERNSHIP APPLICATION PACKET: {packet['title']} - {packet['organization']}")
    out.append(f"Official Portal Link: {packet['canonical_application_url']}\n")
    out.append("--- RESUME BULLETS ---")
    for b in packet.get("tailored_resume_bullets", []):
        out.append(f"- {b}")
    out.append("\n--- COVER LETTER ---")
    out.append(packet.get("cover_letter", ""))
    out.append("\n--- SUBMISSION REMINDER ---")
    out.append(packet.get("human_control_notice", ""))
    return "\n".join(out)
