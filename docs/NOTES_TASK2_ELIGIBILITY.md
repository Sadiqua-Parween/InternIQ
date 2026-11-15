# InternIQ Task 2 Notes: Deterministic Eligibility Engine

**Author:** Mohd Faizan Khan  
**Role:** Evaluation & Verification Engineer (Team HumanBot)  
**Date:** November 2026  
**Status:** Implemented, Tested (`7/7 PASSED`), and Pushed to GitHub  

---

## 1. What Was Done

Implemented `tools/eligibility.py` and unit test suite `tests/unit/test_eligibility.py` strictly satisfying:
- **Functional Requirement FR-05:** Evaluate hard constraints and return `eligible`, `ineligible`, or `unknown` with reasons.
- **Section 7.3 & Table 5 & Table 7:**
  - Hard eligibility is applied **before** ranking.
  - Expired listings are strictly marked `ineligible` with exact date arithmetic evidence.
  - Graduation year mismatch, branch mismatch, and minimum GPA failures are evaluated deterministically.
  - Missing or ambiguous candidate attributes (e.g., student profile has no GPA recorded, or graduation year is absent) produce an explicit `unknown` verdict rather than guessing.
  - Branch matching strips generic academic terms (`engineering`, `tech`, `degree`, `bachelor`) to avoid false positives (e.g., preventing Mechanical Engineering from matching Computer Science & Engineering).

---

## 2. Terminal Commands Executed & Evidence

```bash
# Run deterministic eligibility unit test suite
.venv/bin/pytest tests/unit/test_eligibility.py -v
```

### Execution Output:
```text
tests/unit/test_eligibility.py::test_eligible_candidate PASSED           [ 14%]
tests/unit/test_eligibility.py::test_expired_deadline_disqualifies PASSED [ 28%]
tests/unit/test_eligibility.py::test_graduation_year_mismatch PASSED     [ 42%]
tests/unit/test_eligibility.py::test_branch_mismatch PASSED              [ 57%]
tests/unit/test_eligibility.py::test_min_gpa_failure PASSED              [ 71%]
tests/unit/test_eligibility.py::test_unknown_when_profile_gpa_missing PASSED [ 85%]
tests/unit/test_eligibility.py::test_hard_work_mode_constraint PASSED    [100%]

============================== 7 passed in 0.03s ===============================
VERDICT: PASS
```

---

## 3. How Other Teammates Can Call This Function

For **Samriddhi Raj** (in LangGraph `vet` node) or **Sadiqua Parween**:
```python
from tools.eligibility import check_eligibility
from tools.schemas import Listing, Profile, Preference

# Check eligibility
result = check_eligibility(listing=listing, profile=profile, preference=preference)

if result.verdict == "eligible":
    # Proceed to hybrid ranking
    pass
elif result.verdict == "unknown":
    # Route to human review queue ("needs review")
    pass
else:
    # Disqualified role (result.disqualifiers contains reasons)
    pass
```
