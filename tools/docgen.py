"""
Grounded Application Document Generator
Owner: Mohd Faizan Khan (Team HumanBot)
Domain: Evaluation and Verification

Implements FR-08, Section 6.2 Table 5, and Section 5.2 Node 7:
- Generates tailored resume bullets and cover letter strictly from verified profile facts.
- Interfaces directly with ClaimVerifier to audit every assertion.
- Enforces a 2-attempt regeneration/repair limit if unsupported claims are flagged.
- Rejects hallucinations and returns transparent claim audit trails for student review.
"""

from typing import List, Optional
from datetime import datetime
from tools.schemas import (
    Listing,
    Profile,
    ApplicationDraft,
    ClaimStatus,
)
from agent.verifier import ClaimVerifier


def _generate_raw_resume_bullets(listing: Listing, profile: Profile) -> List[str]:
    """Generates tailored bullet points strictly from confirmed candidate projects and skills."""
    bullets: List[str] = []
    
    # 1. Match candidate projects with listing skills
    req_skills_norm = {s.lower() for s in listing.required_skills}
    for proj in profile.projects:
        proj_skills = [s for s in proj.skills_used if s.lower() in req_skills_norm]
        if proj_skills:
            bullets.append(
                f"Developed {proj.title}: {proj.description} utilizing {', '.join(proj_skills)}."
            )
        else:
            bullets.append(
                f"Engineered {proj.title}: {proj.description}."
            )

    # 2. Add profile skill assertions grounded in confirmed facts
    for fact in profile.confirmed_facts:
        if fact.fact_type in ("skill", "project_achievement"):
            bullets.append(f"{fact.text}.")

    if not bullets:
        bullets.append(f"Demonstrated core proficiency in {', '.join(profile.skills)}.")

    return bullets[:5]  # Keep to top 5 concise bullets


def _generate_raw_cover_letter(listing: Listing, profile: Profile) -> str:
    """Generates a professional cover letter grounded entirely in verified profile attributes."""
    degree_info = profile.education[0].degree if profile.education else "Computer Science"
    inst_info = profile.education[0].institution if profile.education else "University"
    
    # Relevant verified project
    proj_mention = ""
    if profile.projects:
        top_proj = profile.projects[0]
        proj_mention = f" Through my work on {top_proj.title}, I {top_proj.description.lower()}."

    skills_mention = f"My technical foundation includes proficiency in {', '.join(profile.skills[:4])}."

    cover_letter = (
        f"Dear Hiring Team at {listing.organization},\n\n"
        f"I am writing to express my strong interest in the {listing.title} role. "
        f"I am currently pursuing my {degree_info} at {inst_info}.{proj_mention} "
        f"{skills_mention}\n\n"
        f"I am excited to contribute to {listing.organization}'s mission and look forward to discussing my background further.\n\n"
        f"Sincerely,\n{profile.full_name}"
    )
    return cover_letter


def generate_application_draft(
    listing: Listing,
    profile: Profile,
    max_regeneration_attempts: int = 2,
    adversarial_unsupported_text: Optional[str] = None,
) -> ApplicationDraft:
    """
    Generates a role-specific application draft with automated claim-verification loop.
    Enforces the 2-attempt regeneration limit per Section 5.2/5.3.
    """
    verifier = ClaimVerifier(profile)

    bullets = _generate_raw_resume_bullets(listing, profile)
    cover_letter = _generate_raw_cover_letter(listing, profile)

    # Injected adversarial case for verification testing
    if adversarial_unsupported_text:
        bullets.append(adversarial_unsupported_text)

    draft = ApplicationDraft(
        draft_id=f"draft_{listing.listing_id}_{profile.profile_id[:8]}",
        opportunity_id=listing.listing_id,
        profile_id=profile.profile_id,
        version=1,
        tailored_resume_bullets=bullets,
        cover_letter=cover_letter,
        claims=[],
        is_fully_grounded=False,
        unsupported_claim_count=0,
        created_at=datetime.utcnow(),
    )

    # First audit pass
    draft = verifier.audit_draft(draft)

    # Regeneration / repair loop (capped at max_regeneration_attempts)
    attempts = 1
    while not draft.is_fully_grounded and attempts <= max_regeneration_attempts:
        attempts += 1
        draft.version = attempts

        # Filter out bullet points that produced unsupported claims
        unsupported_claim_texts = {
            c.claim_text.strip().lower() for c in draft.claims if c.status == ClaimStatus.UNSUPPORTED
        }
        repaired_bullets = [
            b for b in draft.tailored_resume_bullets
            if b.strip().lower() not in unsupported_claim_texts
        ]

        draft.tailored_resume_bullets = repaired_bullets
        draft = verifier.audit_draft(draft)

    return draft
