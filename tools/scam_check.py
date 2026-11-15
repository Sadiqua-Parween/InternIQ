"""
Scam-Signal Detection Heuristic Engine
Owner: Mohd Faizan Khan (Team HumanBot)
Domain: Evaluation and Verification

Implements FR-07, Section 6.4, and Section 10.5 specifications:
- Identifies potential risk signals: fee requests, free/personal email domains,
  inconsistent organization identity, implausible urgency, sensitive data requests,
  and domain mismatches.
- Outputs non-accusatory heuristic warnings ("possible risk signal") with quoted snippets.
- Avoids definitive claims of fraud.
- Returns strongly-typed ScamCheckResult with risk flags and highest severity.
"""

import re
from urllib.parse import urlparse
from datetime import datetime
from typing import List, Optional
from tools.schemas import Listing, RiskFlag, RiskSeverity, ScamCheckResult


# Regex patterns for heuristic signals
FEE_PATTERNS = [
    r"\b(?:application|registration|training|processing|enrollment|security|laptop)\s+fee\b",
    r"\b(?:refundable|security)\s+deposit\b",
    r"\bpay\s+(?:rs\.?|inr|\$|usd|fees?)\s*\d+",
    r"\b(?:training\s+charges?|payment\s+required|must\s+pay)\b",
    r"\bpay\s+before\s+joining\b",
]

URGENCY_PATTERNS = [
    r"\b(?:immediate\s+hire|instant\s+selection)\s+without\s+interview\b",
    r"\bfirst\s+\d+\s+applicants?\s+only\b",
    r"\boffer\s+expires\s+in\s+\d+\s*(?:hours?|mins?)\b",
    r"\bguaranteed\s+job\s+within\s+24\s+hours\b",
    r"\bno\s+skills?\s+required\s*,\s*high\s+salary\b",
]

SENSITIVE_INFO_PATTERNS = [
    r"\b(?:bank\s+account\s+(?:number|details)|net\s*banking)\b",
    r"\b(?:credit|debit)\s+card\s+number\b",
    r"\b(?:otp|one\s+time\s+password|passwords?|upi\s+pin)\b",
    r"\b(?:send\s+aadhaar|send\s+ssn|social\s+security\s+number)\b",
]

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "rediffmail.com", "aol.com", "yopmail.com", "mailinator.com"
}

GENERIC_SUSPICIOUS_DOMAINS = {
    "blogspot.com", "wordpress.com", "wixsite.com", "weebly.com",
    "tinyurl.com", "bit.ly", "forms.gle", "docs.google.com"
}

SUSPICIOUS_ORG_NAMES = {
    "confidential", "confidential company", "undisclosed",
    "hiring agency", "work from home team", "freelance client",
    "unknown", "immediate hire", "direct company"
}


def check_scam_signals(listing: Listing) -> ScamCheckResult:
    """
    Evaluates an opportunity listing against multi-factor risk heuristics.
    Returns non-accusatory risk flags referencing the exact evidence snippet.
    """
    flags: List[RiskFlag] = []
    text_to_scan = f"{listing.title} {listing.description} {listing.eligibility_text or ''}".lower()

    # 1. Fee Request Detection (High Risk)
    for pattern in FEE_PATTERNS:
        match = re.search(pattern, text_to_scan, re.IGNORECASE)
        if match:
            snippet = match.group(0)
            flags.append(
                RiskFlag(
                    code="FEE_REQUEST",
                    severity=RiskSeverity.HIGH,
                    explanation=(
                        "Possible risk signal: The listing mentions a required fee or financial deposit. "
                        "Legitimate employers rarely ask applicants to pay registration, training, or deposit fees."
                    ),
                    evidence_snippet=snippet,
                    checked_at=datetime.utcnow(),
                )
            )
            break

    # 2. Implausible Urgency or Pressure (Medium Risk)
    for pattern in URGENCY_PATTERNS:
        match = re.search(pattern, text_to_scan, re.IGNORECASE)
        if match:
            snippet = match.group(0)
            flags.append(
                RiskFlag(
                    code="IMPLAUSIBLE_URGENCY",
                    severity=RiskSeverity.MEDIUM,
                    explanation=(
                        "Possible risk signal: The listing uses high-pressure or instant-selection urgency phrases. "
                        "Applicants should verify the employer's standard hiring process."
                    ),
                    evidence_snippet=snippet,
                    checked_at=datetime.utcnow(),
                )
            )
            break

    # 3. Sensitive Information Requests (High Risk)
    for pattern in SENSITIVE_INFO_PATTERNS:
        match = re.search(pattern, text_to_scan, re.IGNORECASE)
        if match:
            snippet = match.group(0)
            flags.append(
                RiskFlag(
                    code="SENSITIVE_INFO_REQUEST",
                    severity=RiskSeverity.HIGH,
                    explanation=(
                        "Possible risk signal: The listing appears to request sensitive financial or identity details "
                        "(e.g., bank account, OTP, card details, or PIN) prior to legitimate employment onboarding."
                    ),
                    evidence_snippet=snippet,
                    checked_at=datetime.utcnow(),
                )
            )
            break

    # 4. Personal Email Only Detection (Medium Risk)
    email_matches = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text_to_scan)
    for email in email_matches:
        domain = email.split("@")[-1].lower()
        if domain in FREE_EMAIL_DOMAINS:
            # Check if organization claims to be an established corporate firm
            org_name = listing.organization.strip()
            if len(org_name) > 3 and org_name.lower() not in SUSPICIOUS_ORG_NAMES:
                flags.append(
                    RiskFlag(
                        code="UNVERIFIED_EMAIL_DOMAIN",
                        severity=RiskSeverity.MEDIUM,
                        explanation=(
                            f"Possible risk signal: The recruiter contact email '{email}' uses a public free provider "
                            f"({domain}) rather than an official corporate domain for '{org_name}'."
                        ),
                        evidence_snippet=email,
                        checked_at=datetime.utcnow(),
                    )
                )
                break

    # 5. Inconsistent / Missing Organization Identity (Low/Medium Risk)
    org_clean = listing.organization.strip().lower()
    if not org_clean or org_clean in SUSPICIOUS_ORG_NAMES:
        flags.append(
            RiskFlag(
                code="INCONSISTENT_ORG_IDENTITY",
                severity=RiskSeverity.LOW,
                explanation=(
                    "Possible risk signal: The employer identity is missing, generic, or listed as confidential. "
                    "Confirm the registered legal entity before submitting personal application materials."
                ),
                evidence_snippet=listing.organization or "EMPTY_ORG_FIELD",
                checked_at=datetime.utcnow(),
            )
        )

    # 6. Domain Mismatch / Unofficial Hosting (Medium Risk)
    try:
        parsed_url = urlparse(listing.canonical_url)
        url_netloc = parsed_url.netloc.lower()
        if any(susp in url_netloc for susp in GENERIC_SUSPICIOUS_DOMAINS):
            flags.append(
                RiskFlag(
                    code="DOMAIN_MISMATCH",
                    severity=RiskSeverity.MEDIUM,
                    explanation=(
                        f"Possible risk signal: The application URL points to a third-party form or free host "
                        f"('{url_netloc}') rather than an official company domain."
                    ),
                    evidence_snippet=listing.canonical_url,
                    checked_at=datetime.utcnow(),
                )
            )
    except Exception:
        pass

    # Determine highest severity
    highest_severity: Optional[RiskSeverity] = None
    if any(f.severity == RiskSeverity.HIGH for f in flags):
        highest_severity = RiskSeverity.HIGH
    elif any(f.severity == RiskSeverity.MEDIUM for f in flags):
        highest_severity = RiskSeverity.MEDIUM
    elif any(f.severity == RiskSeverity.LOW for f in flags):
        highest_severity = RiskSeverity.LOW

    is_suspicious = highest_severity in (RiskSeverity.HIGH, RiskSeverity.MEDIUM)

    if not flags:
        summary = "No risk signals detected. Always verify official corporate channels."
    else:
        summary = (
            f"Flagged {len(flags)} possible risk signal(s) [Highest severity: {highest_severity.value.upper()}]. "
            "Verification recommended before sharing private information or documents."
        )

    return ScamCheckResult(
        is_suspicious=is_suspicious,
        flags=flags,
        highest_severity=highest_severity,
        verdict_summary=summary,
    )
