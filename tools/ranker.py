"""
Hybrid Matching and Transparent Ranking Engine
Owner: Mohd Faizan Khan (Team HumanBot)
Domain: Evaluation and Verification

Implements FR-06 and Table 7 / Section 7.3 specifications:
- Hybrid 4-factor scoring:
    1. Skills Match (Weight: 0.35)
    2. Semantic Fit (Weight: 0.35, sentence-transformers/all-MiniLM-L6-v2)
    3. Preference Fit (Weight: 0.20)
    4. Deadline Urgency (Weight: 0.10)
- Invariant: Excluded or missing factors are removed from the denominator and
  weights are renormalized.
- Invariant: If no usable factors exist, score is None (review-only), not zero.
- Complete skill-gap analysis: matched skills, missing required skills, evidence coverage.
"""

from datetime import datetime, date
from typing import List, Dict, Tuple, Optional, Any
import numpy as np

from tools.schemas import (
    Listing,
    Profile,
    Preference,
    ScoreBreakdown,
    WorkMode,
)

# Ranking formula version and default starting weights
RANKER_VERSION = "ranker_v1"
DEFAULT_WEIGHTS: Dict[str, float] = {
    "skills": 0.35,
    "semantic_fit": 0.35,
    "preference_fit": 0.20,
    "deadline": 0.10,
}

_EMBEDDING_MODEL = None
_EMBEDDING_FAILED = False


def _get_embedding_model():
    """Lazy loader for SentenceTransformer with graceful fallback."""
    global _EMBEDDING_MODEL, _EMBEDDING_FAILED
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL
    if _EMBEDDING_FAILED:
        return None

    try:
        from sentence_transformers import SentenceTransformer
        _EMBEDDING_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return _EMBEDDING_MODEL
    except Exception:
        _EMBEDDING_FAILED = True
        return None


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Calculates cosine similarity between two 1D vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def _tf_idf_semantic_fallback(text_a: str, text_b: str) -> float:
    """Deterministic TF-IDF cosine similarity fallback if deep model weights not cached."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    try:
        tfidf = vectorizer.fit_transform([text_a, text_b]).toarray()
        return _cosine_similarity(tfidf[0], tfidf[1])
    except Exception:
        return 0.0


def _normalize_token(s: str) -> str:
    return "".join(c.lower() for c in s if c.isalnum() or c.isspace()).strip()


def calculate_skills_factor(
    listing: Listing,
    profile: Profile,
) -> Tuple[Optional[float], List[str], List[str], float]:
    """
    Computes skills match factor and skill gaps.
    Returns: (score, matched_skills, missing_skills, evidence_coverage)
    """
    if not listing.required_skills:
        return None, [], [], 1.0

    profile_skills_norm = {_normalize_token(s) for s in profile.skills}
    # Also check project skills
    for proj in profile.projects:
        for ps in proj.skills_used:
            profile_skills_norm.add(_normalize_token(ps))

    matched: List[str] = []
    missing: List[str] = []

    for req in listing.required_skills:
        norm_req = _normalize_token(req)
        # Check direct or substring match
        if any(norm_req == ps or norm_req in ps or ps in norm_req for ps in profile_skills_norm):
            matched.append(req)
        else:
            missing.append(req)

    total_req = len(listing.required_skills)
    coverage = len(matched) / total_req if total_req > 0 else 1.0
    score = coverage  # In ranker_v1, normalized required skill match fraction

    return score, matched, missing, coverage


def calculate_semantic_factor(
    listing: Listing,
    profile: Profile,
    preference: Optional[Preference] = None,
) -> Optional[float]:
    """
    Computes semantic similarity mapped linearly from [-1, 1] to [0, 1] and clipped.
    Uses candidate summary (goals + skills + projects) vs job description + title.
    """
    # Build candidate representation
    cand_parts = [profile.full_name]
    if preference and preference.target_roles:
        cand_parts.append("Target roles: " + ", ".join(preference.target_roles))
    if preference and preference.domains:
        cand_parts.append("Interests: " + ", ".join(preference.domains))
    if profile.skills:
        cand_parts.append("Skills: " + ", ".join(profile.skills))
    for proj in profile.projects:
        cand_parts.append(f"Project: {proj.title}. {proj.description}")
    cand_text = " ".join(cand_parts).strip()

    job_text = f"{listing.title}. {listing.organization}. {listing.description}".strip()
    if not job_text or not cand_text:
        return None

    model = _get_embedding_model()
    if model is not None:
        try:
            embeddings = model.encode([cand_text, job_text])
            raw_sim = _cosine_similarity(embeddings[0], embeddings[1])
        except Exception:
            raw_sim = _tf_idf_semantic_fallback(cand_text, job_text)
    else:
        raw_sim = _tf_idf_semantic_fallback(cand_text, job_text)

    # Linear mapping from [-1, 1] to [0, 1], clipped
    norm_sim = float(np.clip((raw_sim + 1.0) / 2.0, 0.0, 1.0))
    return norm_sim


def calculate_preference_factor(
    listing: Listing,
    preference: Optional[Preference],
) -> Tuple[Optional[float], List[str]]:
    """
    Computes preference fit = satisfied soft preferences / assessable configured preferences.
    Missing listing values are unavailable, not failures.
    """
    if not preference:
        return None, ["No preferences configured; factor unavailable"]

    explanations: List[str] = []
    satisfied = 0
    assessable = 0

    # 1. Target Role match
    if preference.target_roles:
        assessable += 1
        listing_title_norm = _normalize_token(listing.title)
        role_matched = any(_normalize_token(role) in listing_title_norm or listing_title_norm in _normalize_token(role) for role in preference.target_roles)
        if role_matched:
            satisfied += 1
            explanations.append(f"Role match: '{listing.title}' matches target roles")
        else:
            explanations.append(f"Role non-match: '{listing.title}' not in target roles")

    # 2. Domain / Industry match
    if preference.domains:
        assessable += 1
        desc_norm = _normalize_token(f"{listing.title} {listing.description}")
        domain_matched = any(_normalize_token(d) in desc_norm for d in preference.domains)
        if domain_matched:
            satisfied += 1
            explanations.append("Domain match: Job aligns with target domain")
        else:
            explanations.append("Domain non-match: Job does not contain target domain keywords")

    # 3. Location match
    if preference.locations and listing.locations:
        assessable += 1
        loc_pref_norm = {_normalize_token(l) for l in preference.locations}
        listing_loc_norm = {_normalize_token(l) for l in listing.locations}
        if listing.work_mode == WorkMode.REMOTE or any(lp in listing_loc_norm or any(lp in ll for ll in listing_loc_norm) for lp in loc_pref_norm):
            satisfied += 1
            explanations.append(f"Location match: Role location {listing.locations} aligns with preferences")
        else:
            explanations.append(f"Location non-match: {listing.locations} not in preferred locations")

    # 4. Work mode match
    if preference.work_modes and listing.work_mode != WorkMode.UNKNOWN:
        assessable += 1
        if listing.work_mode in preference.work_modes:
            satisfied += 1
            explanations.append(f"Work mode match: {listing.work_mode.value} is accepted")
        else:
            explanations.append(f"Work mode non-match: {listing.work_mode.value} not preferred")

    # 5. Stipend preference
    if preference.min_stipend is not None and listing.stipend is not None:
        assessable += 1
        if listing.stipend >= preference.min_stipend:
            satisfied += 1
            explanations.append(f"Stipend match: {listing.stipend} >= min {preference.min_stipend}")
        else:
            explanations.append(f"Stipend lower than desired: {listing.stipend} < min {preference.min_stipend}")

    if assessable == 0:
        return None, ["No assessable preferences against listing attributes"]

    score = satisfied / assessable
    return score, explanations


def calculate_deadline_factor(
    listing: Listing,
    current_date: Optional[date] = None,
) -> Tuple[Optional[float], Optional[str]]:
    """
    For unexpired listings with deadline: D = 1 - min(days_remaining / 30, 1).
    Missing deadline is unavailable and excluded from weighted denominator.
    """
    if not listing.deadline:
        return None, "Deadline unspecified in listing (factor unavailable)"

    if current_date is None:
        current_date = datetime.utcnow().date()

    try:
        clean_deadline = listing.deadline.strip().split("T")[0]
        deadline_date = datetime.strptime(clean_deadline, "%Y-%m-%d").date()
    except Exception:
        return None, f"Could not parse deadline '{listing.deadline}'"

    days_remaining = (deadline_date - current_date).days
    if days_remaining < 0:
        # Expired roles should be eliminated by eligibility check; return 0.0 if assessed here
        return 0.0, f"Deadline expired {abs(days_remaining)} days ago"

    # Formula per Table 7: D = 1 - min(days_remaining / 30, 1)
    urgency = 1.0 - min(days_remaining / 30.0, 1.0)
    return urgency, f"{days_remaining} days remaining (Urgency score: {urgency:.2f})"


def score_opportunity(
    listing: Listing,
    profile: Profile,
    preference: Optional[Preference] = None,
    current_date: Optional[date] = None,
    custom_weights: Optional[Dict[str, float]] = None,
) -> ScoreBreakdown:
    """
    Computes transparent hybrid match score with step-by-step audit explanations.
    """
    weights = dict(custom_weights or DEFAULT_WEIGHTS)
    explanations: List[str] = []

    # 1. Skills factor
    skills_score, matched_skills, missing_skills, coverage = calculate_skills_factor(listing, profile)
    if skills_score is not None:
        explanations.append(f"Skills factor: {skills_score:.2f} ({len(matched_skills)} matched, {len(missing_skills)} missing, coverage={coverage:.2f})")
    else:
        explanations.append("Skills factor: Unavailable (listing has no required skills listed)")

    # 2. Semantic fit factor
    semantic_score = calculate_semantic_factor(listing, profile, preference)
    if semantic_score is not None:
        explanations.append(f"Semantic fit factor: {semantic_score:.2f} (Sentence-Transformers all-MiniLM-L6-v2)")
    else:
        explanations.append("Semantic fit factor: Unavailable")

    # 3. Preference fit factor
    pref_score, pref_expl = calculate_preference_factor(listing, preference)
    if pref_score is not None:
        explanations.append(f"Preference fit factor: {pref_score:.2f} ({', '.join(pref_expl)})")
    else:
        explanations.append("Preference fit factor: Unavailable")

    # 4. Deadline factor
    deadline_score, deadline_expl = calculate_deadline_factor(listing, current_date)
    if deadline_score is not None:
        explanations.append(f"Deadline urgency factor: {deadline_score:.2f} ({deadline_expl})")
    else:
        explanations.append(f"Deadline urgency factor: {deadline_expl}")

    factor_scores: Dict[str, Optional[float]] = {
        "skills": skills_score,
        "semantic_fit": semantic_score,
        "preference_fit": pref_score,
        "deadline": deadline_score,
    }

    # Weight renormalization over available factors
    available_factors = {k: v for k, v in factor_scores.items() if v is not None}
    sum_available_weights = sum(weights[k] for k in available_factors)

    if sum_available_weights > 0:
        normalized_weights = {k: weights[k] / sum_available_weights for k in available_factors}
        composite_score = sum(normalized_weights[k] * available_factors[k] for k in available_factors)
        composite_score = float(np.clip(composite_score, 0.0, 1.0))
        explanations.append(
            f"Composite Score: {composite_score:.4f} (renormalized across {list(available_factors.keys())})"
        )
    else:
        normalized_weights = {}
        composite_score = None
        explanations.append("Composite Score: None (No usable factors available for ranking)")

    return ScoreBreakdown(
        factor_scores=factor_scores,
        weights_version=RANKER_VERSION,
        weights_used=normalized_weights,
        total_score=composite_score,
        missing_skills=missing_skills,
        matched_skills=matched_skills,
        evidence_coverage=coverage,
        explanations=explanations,
    )


def rank_opportunities(
    listings: List[Listing],
    profile: Profile,
    preference: Optional[Preference] = None,
    current_date: Optional[date] = None,
) -> List[Tuple[Listing, ScoreBreakdown]]:
    """
    Ranks multiple listings by composite score in descending order.
    Unranked (None score) items are placed at the end.
    """
    scored = []
    for l in listings:
        sb = score_opportunity(l, profile, preference, current_date=current_date)
        scored.append((l, sb))

    # Sort descending by total_score (handling None)
    scored.sort(
        key=lambda item: (item[1].total_score is not None, item[1].total_score or -1.0),
        reverse=True,
    )
    return scored
