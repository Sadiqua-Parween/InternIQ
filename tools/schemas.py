"""
InternIQ Core Pydantic Schemas and Domain Models
Specification based on InternIQ Technical Report (Appendix B, Section 6.3, Table 5, Table 6).

All tool boundaries and inter-agent messages are strongly typed, serializable,
and validated using Pydantic V2.
"""

from __future__ import annotations
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class WorkMode(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"
    FLEXIBLE = "flexible"
    UNKNOWN = "unknown"


class EligibilityVerdict(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"


class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"


class UserDecision(str, Enum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    CANCEL = "cancel"


class TrackerEventType(str, Enum):
    SAVED = "saved"
    SHORTLISTED = "shortlisted"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


# =====================================================================
# Profile & Candidate Models
# =====================================================================

class Education(BaseModel):
    degree: str = Field(..., description="Degree name, e.g. B.Tech Computer Science")
    institution: str = Field(..., description="College / University name")
    branch: Optional[str] = Field(None, description="Department or Branch of study")
    graduation_year: int = Field(..., description="Expected or completed graduation year")
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0, description="CGPA out of 10 or scale")
    max_cgpa: float = Field(10.0, description="Maximum scale, e.g. 10.0 or 4.0")
    is_verified: bool = Field(True, description="Whether confirmed by student")


class Skill(BaseModel):
    name: str = Field(..., description="Normalized skill name")
    category: Optional[str] = Field(None, description="e.g. Programming Language, Framework, Tool")
    years_experience: Optional[float] = Field(None, description="Estimated years of experience")
    evidence_source: Optional[str] = Field(None, description="Provenance in profile/resume")


class Project(BaseModel):
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Summary of project work and impact")
    skills_used: List[str] = Field(default_factory=list, description="Technologies / skills applied")
    live_url: Optional[str] = Field(None, description="Demo or project link")
    repo_url: Optional[str] = Field(None, description="Repository link")
    role: Optional[str] = Field(None, description="Candidate role in project")


class EvidenceFact(BaseModel):
    """
    Atomic verified fact from candidate profile used for zero-hallucination claim audit.
    """
    fact_id: str = Field(..., description="Unique fact identifier, e.g. fact_python_exp")
    fact_type: str = Field(..., description="e.g. skill, project_achievement, education_metric")
    text: str = Field(..., description="Exact factual assertion confirmed by student")
    source_doc: str = Field("user_profile", description="Source document or confirmation reference")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    confirmed_by_user: bool = Field(True, description="Explicit student confirmation")


class Profile(BaseModel):
    profile_id: str = Field(..., description="Unique student profile ID")
    full_name: str = Field(..., description="Student full name")
    email: str = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list, description="List of recognized skill strings")
    projects: List[Project] = Field(default_factory=list)
    confirmed_facts: List[EvidenceFact] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Preference(BaseModel):
    profile_id: str = Field(..., description="Associated profile ID")
    target_roles: List[str] = Field(default_factory=list, description="Target titles, e.g. Machine Learning Intern")
    domains: List[str] = Field(default_factory=list, description="Preferred domains, e.g. AI, Backend, FinTech")
    locations: List[str] = Field(default_factory=list, description="Preferred cities or 'Remote'")
    work_modes: List[WorkMode] = Field(default_factory=lambda: [WorkMode.REMOTE, WorkMode.HYBRID])
    min_stipend: Optional[float] = Field(None, description="Minimum expected stipend in INR/month")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Custom soft or hard constraints")


# =====================================================================
# Opportunity & Listing Models
# =====================================================================

class Listing(BaseModel):
    """
    Normalized opportunity listing snapshot with full provenance.
    """
    listing_id: str = Field(..., description="Deterministic or unique listing identifier")
    source_id: str = Field(..., description="Source name, e.g. greenhouse, lever, unstop, manual_csv")
    source_record_id: str = Field(..., description="Identifier in original source")
    canonical_url: str = Field(..., description="Canonical source URL")
    title: str = Field(..., description="Role title")
    organization: str = Field(..., description="Hiring organization / company")
    description: str = Field(..., description="Plain-text job description (scripts stripped)")
    locations: List[str] = Field(default_factory=list)
    work_mode: WorkMode = Field(WorkMode.UNKNOWN)
    start_date: Optional[str] = Field(None, description="Expected start date string or ISO date")
    deadline: Optional[str] = Field(None, description="Application deadline ISO date (YYYY-MM-DD)")
    eligibility_text: Optional[str] = Field(None, description="Raw eligibility clause from posting")
    min_gpa: Optional[float] = Field(None, description="Minimum CGPA/GPA if specified")
    eligible_branches: List[str] = Field(default_factory=list, description="Permitted degrees/branches")
    eligible_years: List[int] = Field(default_factory=list, description="Eligible graduation years (e.g. 2026, 2027)")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    stipend: Optional[float] = Field(None, description="Monthly stipend amount")
    currency: str = Field("INR", description="ISO-4217 currency code")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    content_hash: str = Field("", description="SHA-256 hash of title+org+description for deduplication")


# =====================================================================
# Eligibility & Vetting Models
# =====================================================================

class EligibilityResult(BaseModel):
    verdict: EligibilityVerdict
    reasons: List[str] = Field(default_factory=list, description="Explanations for verdict")
    evidence: List[str] = Field(default_factory=list, description="Direct quotes or data points evaluated")
    disqualifiers: List[str] = Field(default_factory=list, description="Failed hard constraints")
    unknown_factors: List[str] = Field(default_factory=list, description="Factors that could not be evaluated")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


# =====================================================================
# Scam-Signal Detection Models
# =====================================================================

class RiskFlag(BaseModel):
    code: str = Field(..., description="Risk rule code, e.g. FEE_REQUEST, UNVERIFIED_EMAIL_DOMAIN")
    severity: RiskSeverity = Field(..., description="low, medium, high")
    explanation: str = Field(..., description="Heuristic explanation with supporting context")
    evidence_snippet: str = Field(..., description="Quoted snippet from listing triggering flag")
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class ScamCheckResult(BaseModel):
    is_suspicious: bool = Field(False, description="True if any high/medium risk signals detected")
    flags: List[RiskFlag] = Field(default_factory=list)
    highest_severity: Optional[RiskSeverity] = None
    verdict_summary: str = Field("No risk signals detected.", description="Non-accusatory risk summary")


# =====================================================================
# Transparent Ranking & Scoring Models
# =====================================================================

class ScoreBreakdown(BaseModel):
    factor_scores: Dict[str, Optional[float]] = Field(
        ...,
        description="Factor scores: skills, semantic_fit, preference_fit, deadline. None if unavailable."
    )
    weights_version: str = Field("ranker_v1", description="Ranking formula and weights version")
    weights_used: Dict[str, float] = Field(..., description="Effective weights after renormalizing missing factors")
    total_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Composite score in [0.0, 1.0], or None if no usable factors."
    )
    missing_skills: List[str] = Field(default_factory=list, description="Required skills absent in candidate profile")
    matched_skills: List[str] = Field(default_factory=list, description="Required skills confirmed in candidate profile")
    evidence_coverage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of required skills with confirmed profile evidence"
    )
    explanations: List[str] = Field(default_factory=list, description="Step-by-step transparent score calculations")


# =====================================================================
# Document Generation & Claim Audit Models
# =====================================================================

class ClaimAudit(BaseModel):
    claim_id: str = Field(..., description="Unique claim ID within draft")
    claim_text: str = Field(..., description="Sentence or clause asserting a factual claim")
    claim_type: str = Field(..., description="skill, metric, achievement, credential, experience")
    supporting_fact_ids: List[str] = Field(
        default_factory=list,
        description="IDs of confirmed profile facts supporting this claim"
    )
    status: ClaimStatus = Field(..., description="supported, unsupported, ambiguous")
    audit_note: str = Field("", description="Verifier audit commentary or evidence trail")


class ApplicationDraft(BaseModel):
    draft_id: str = Field(..., description="Unique draft identifier")
    opportunity_id: str = Field(..., description="Target listing ID")
    profile_id: str = Field(..., description="Candidate profile ID")
    version: int = Field(1, description="Draft iteration / attempt number")
    tailored_resume_bullets: List[str] = Field(default_factory=list)
    cover_letter: str = Field("", description="Tailored cover letter text")
    claims: List[ClaimAudit] = Field(default_factory=list, description="Audited claims list")
    is_fully_grounded: bool = Field(False, description="True only if unsupported claim count is zero")
    unsupported_claim_count: int = Field(0, description="Count of unsupported claims")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = Field(None, description="Timestamp of student approval")


# =====================================================================
# Human Approval & Tracker Models
# =====================================================================

class Approval(BaseModel):
    run_id: str
    opportunity_id: str
    action: str = Field(..., description="e.g. save_draft, update_tracker")
    user_decision: UserDecision = Field(..., description="approve, edit, reject, cancel")
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    edited_fields: Dict[str, str] = Field(default_factory=dict)
    approval_token: Optional[str] = Field(None, description="Cryptographic or idempotent approval token")


class TrackerEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    opportunity_id: str = Field(..., description="Listing ID")
    event_type: TrackerEventType = Field(..., description="Current status")
    event_time: datetime = Field(default_factory=datetime.utcnow)
    user_confirmed: bool = Field(True, description="Must be confirmed by student")
    idempotency_key: str = Field(..., description="Idempotent key preventing duplicate events")
    notes: Optional[str] = Field(None, description="User notes or interview updates")
