"""
Deterministic Eligibility Verification Engine
Owner: Mohd Faizan Khan (Team HumanBot)
Domain: Evaluation and Verification

Implements FR-05 and Table 5 / Section 7.3 specifications:
- Hard rule evaluation: deadline, graduation year, degree/branch, minimum CGPA, work mode.
- Strict three-state verdict: ELIGIBLE, INELIGIBLE, UNKNOWN.
- Never guesses missing or ambiguous values; treats absent profile/listing info as UNKNOWN.
- Expired deadlines are hard disqualifiers evaluated before ranking.
- Produces auditable EligibilityResult with explicit reasons, evidence, and disqualifiers.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from tools.schemas import (
    Listing,
    Profile,
    Preference,
    EligibilityResult,
    EligibilityVerdict,
    WorkMode,
)


def _parse_iso_date(date_str: Optional[str]) -> Optional[date]:
    """Safely parse YYYY-MM-DD or ISO format string to date."""
    if not date_str:
        return None
    try:
        clean_str = date_str.strip().split("T")[0]
        return datetime.strptime(clean_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


GENERIC_ACADEMIC_TERMS = {
    "engineering", "engineer", "technology", "tech", "btech", "mtech",
    "bachelor", "bachelors", "master", "masters", "degree", "bs", "ms",
    "department", "dept", "studies", "science", "sciences"
}


def _normalize_string(val: str) -> str:
    """Normalize string for casing and punctuation-insensitive matching."""
    return "".join(c.lower() for c in val if c.isalnum() or c.isspace()).strip()


def _extract_core_branch_terms(branch_str: str) -> set[str]:
    """Extract informative non-generic discipline tokens."""
    tokens = [t.strip() for t in _normalize_string(branch_str).split()]
    core = {t for t in tokens if t not in GENERIC_ACADEMIC_TERMS and len(t) > 2}
    return core or set(tokens)


def _check_branch_match(req_branch: str, student_branches: List[str], student_degrees: List[str]) -> bool:
    norm_req = _normalize_string(req_branch)
    req_core = _extract_core_branch_terms(req_branch)

    for student_text in (student_branches + student_degrees):
        norm_student = _normalize_string(student_text)
        if norm_req in norm_student or norm_student in norm_req:
            return True
        student_core = _extract_core_branch_terms(student_text)
        if req_core and req_core.issubset(student_core):
            return True
        # If discipline like "mechanical" or "civil" or "electrical" is required, it must be present
        if req_core and any(c in student_core for c in req_core):
            # Check if multi-word specific discipline matches
            if len(req_core) == 1:
                return True
            # For multi-word, at least half of core tokens match
            overlap = req_core.intersection(student_core)
            if len(overlap) >= len(req_core) / 2:
                return True

    return False


def check_eligibility(
    listing: Listing,
    profile: Profile,
    preference: Optional[Preference] = None,
    current_date: Optional[date] = None,
) -> EligibilityResult:
    """
    Evaluates hard constraints deterministically against student profile.
    
    Invariants:
    1. If any hard constraint fails -> INELIGIBLE (with exact disqualifier).
    2. Expired deadline -> INELIGIBLE.
    3. If required criteria are missing from profile or ambiguous -> UNKNOWN (needs review).
    4. If all evaluated criteria satisfy requirements and no unknowns -> ELIGIBLE.
    """
    if current_date is None:
        current_date = datetime.utcnow().date()

    reasons: List[str] = []
    evidence: List[str] = []
    disqualifiers: List[str] = []
    unknown_factors: List[str] = []

    # 1. Deadline Expiration Check
    deadline_date = _parse_iso_date(listing.deadline)
    if deadline_date:
        if deadline_date < current_date:
            disq = f"Application deadline expired on {deadline_date} (Current reference date: {current_date})"
            disqualifiers.append(disq)
            reasons.append(disq)
            evidence.append(f"Listing deadline: {listing.deadline}")
        else:
            days_left = (deadline_date - current_date).days
            reasons.append(f"Application deadline is valid ({days_left} days remaining until {deadline_date})")
            evidence.append(f"Listing deadline: {listing.deadline}")
    else:
        unknown_factors.append("Deadline is unspecified in listing")
        reasons.append("Deadline is unspecified in listing (assumed open but unverified)")

    # 2. Graduation Year Check
    student_grad_years = [edu.graduation_year for edu in profile.education if edu.graduation_year]
    if listing.eligible_years:
        if not student_grad_years:
            unknown_factors.append("Candidate graduation year is unspecified in profile")
            reasons.append(f"Role requires graduation year in {listing.eligible_years}, but student year is not provided")
        else:
            matches_year = any(y in listing.eligible_years for y in student_grad_years)
            if not matches_year:
                disq = f"Graduation year mismatch: Student year(s) {student_grad_years} not in required years {listing.eligible_years}"
                disqualifiers.append(disq)
                reasons.append(disq)
                evidence.append(f"Profile grad years: {student_grad_years}; Required: {listing.eligible_years}")
            else:
                reasons.append(f"Graduation year satisfied: matches eligible years {listing.eligible_years}")
                evidence.append(f"Profile grad years: {student_grad_years}")

    # 3. Branch / Major Check
    student_branches = [edu.branch for edu in profile.education if edu.branch]
    student_degrees = [edu.degree for edu in profile.education if edu.degree]
    combined_education_text = " ".join(student_branches + student_degrees)

    if listing.eligible_branches:
        if not student_branches and not student_degrees:
            unknown_factors.append("Candidate branch / degree is unspecified in profile")
            reasons.append(f"Role requires branch in {listing.eligible_branches}, but student degree/branch is missing")
        else:
            matches_branch = any(
                _check_branch_match(req_b, student_branches, student_degrees)
                for req_b in listing.eligible_branches
            )

            if not matches_branch:
                disq = f"Eligible branch requirement not met: Required {listing.eligible_branches}, Student education: '{combined_education_text}'"
                disqualifiers.append(disq)
                reasons.append(disq)
                evidence.append(f"Profile education: {combined_education_text}; Required branches: {listing.eligible_branches}")
            else:
                reasons.append(f"Degree/branch matches required criteria ({listing.eligible_branches})")
                evidence.append(f"Profile education: {combined_education_text}")

    # 4. Minimum GPA / CGPA Check
    student_cgpas = [edu.cgpa for edu in profile.education if edu.cgpa is not None]
    if listing.min_gpa is not None:
        if not student_cgpas:
            unknown_factors.append("Candidate CGPA/GPA is unspecified in profile")
            reasons.append(f"Role requires minimum GPA/CGPA of {listing.min_gpa}, but student profile has no GPA recorded")
        else:
            best_student_cgpa = max(student_cgpas)
            if best_student_cgpa < listing.min_gpa:
                disq = f"Minimum CGPA not met: Student has {best_student_cgpa:.2f}, role requires {listing.min_gpa:.2f}"
                disqualifiers.append(disq)
                reasons.append(disq)
                evidence.append(f"Profile CGPA: {best_student_cgpa}; Required min GPA: {listing.min_gpa}")
            else:
                reasons.append(f"CGPA requirement met: {best_student_cgpa:.2f} >= {listing.min_gpa:.2f}")
                evidence.append(f"Profile CGPA: {best_student_cgpa}")

    # 5. Work Mode / Location Hard Constraint Check
    if preference:
        # Check hard work mode preference if specified in preference.constraints
        hard_mode_required = preference.constraints.get("hard_work_mode", False)
        if hard_mode_required and preference.work_modes:
            if listing.work_mode != WorkMode.UNKNOWN and listing.work_mode not in preference.work_modes:
                disq = f"Work mode conflict: Role is '{listing.work_mode.value}', but student strictly requires {[m.value for m in preference.work_modes]}"
                disqualifiers.append(disq)
                reasons.append(disq)
                evidence.append(f"Listing work mode: {listing.work_mode.value}")

    # 6. Synthesize Verdict
    if disqualifiers:
        verdict = EligibilityVerdict.INELIGIBLE
    elif unknown_factors:
        verdict = EligibilityVerdict.UNKNOWN
    else:
        verdict = EligibilityVerdict.ELIGIBLE

    return EligibilityResult(
        verdict=verdict,
        reasons=reasons,
        evidence=evidence,
        disqualifiers=disqualifiers,
        unknown_factors=unknown_factors,
        evaluated_at=datetime.utcnow(),
    )
