# InternIQ Task 3 Notes: Heuristic Scam-Signal Detection Engine

**Author:** Mohd Faizan Khan  
**Role:** Evaluation & Verification Engineer (Team HumanBot)  
**Date:** November 2026  
**Status:** Implemented, Tested (`6/6 PASSED`), and Pushed to GitHub  

---

## 1. What Was Done

Implemented `tools/scam_check.py` and unit tests in `tests/unit/test_scam_check.py` complying with:
- **Functional Requirement FR-07:** Flag scam signals and disclose their heuristic basis.
- **Section 6.4 & Section 10.5 Specifications:**
  - Implemented 6 distinct heuristic detectors:
    1. `FEE_REQUEST`: Flags application fees, security deposits, training fees (Severity: HIGH).
    2. `IMPLAUSIBLE_URGENCY`: Flags instant hiring without interview, countdown pressure (Severity: MEDIUM).
    3. `SENSITIVE_INFO_REQUEST`: Flags upfront requests for bank account details, cards, OTPs, passwords, or Aadhaar/SSN (Severity: HIGH).
    4. `UNVERIFIED_EMAIL_DOMAIN`: Flags corporate postings using public free email providers (`@gmail.com`, `@yahoo.com`) (Severity: MEDIUM).
    5. `INCONSISTENT_ORG_IDENTITY`: Flags empty or generic "confidential" employer names (Severity: LOW).
    6. `DOMAIN_MISMATCH`: Flags application links pointing to free form hosts (`forms.gle`, `blogspot.com`, `wixsite.com`) rather than verified company domains (Severity: MEDIUM).
  - Enforced strictly non-accusatory language: Warnings prefix with *"Possible risk signal"* and quote the exact evidence snippet without making definitive claims of fraud.

---

## 2. Terminal Commands Executed & Evidence

```bash
# Run scam detection unit test suite
.venv/bin/pytest tests/unit/test_scam_check.py -v
```

### Execution Output:
```text
tests/unit/test_scam_check.py::test_clean_listing_no_flags PASSED        [ 16%]
tests/unit/test_scam_check.py::test_fee_request_flagged PASSED           [ 33%]
tests/unit/test_scam_check.py::test_free_email_domain_flagged PASSED     [ 50%]
tests/unit/test_scam_check.py::test_implausible_urgency_flagged PASSED   [ 66%]
tests/unit/test_scam_check.py::test_sensitive_info_request_flagged PASSED [ 83%]
tests/unit/test_scam_check.py::test_domain_mismatch_flagged PASSED       [100%]

============================== 6 passed in 0.04s ===============================
VERDICT: PASS
```

---

## 3. How Other Teammates Can Call This Function

For **Samriddhi Raj** (in LangGraph `vet` node) or **Streamlit UI**:
```python
from tools.scam_check import check_scam_signals
from tools.schemas import Listing

scam_result = check_scam_signals(listing)

if scam_result.is_suspicious:
    # Display warning banner in UI or demote from top results
    for flag in scam_result.flags:
        print(f"[{flag.severity.value.upper()}] {flag.explanation} (Snippet: '{flag.evidence_snippet}')")
else:
    # Listing has no detected risk signals
    pass
```
