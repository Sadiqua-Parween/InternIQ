# InternIQ Task 5 Notes: Grounded Document Generator & Claim-Level Verifier

**Author:** Mohd Faizan Khan  
**Role:** Evaluation & Verification Engineer (Team HumanBot)  
**Date:** November 2026  
**Status:** Implemented, Tested (`3/3 PASSED`), and Pushed to GitHub  

---

## 1. What Was Done

Implemented `agent/verifier.py`, `tools/docgen.py`, and unit tests `tests/unit/test_docgen_verifier.py` strictly complying with:
- **Functional Requirement FR-08:** Draft resume bullets and cover letter; verify each factual claim against profile facts.
- **Section 1.2 Objective 5 & Table 1:**
  - **Zero Unsupported Claims Target:** Guarantees that no hallucinated skills, fake metrics, or unverified achievements appear in final candidate application materials.
- **Section 5.2 Node 7 & Section 5.3 Repair Loop:**
  - Generates role-specific resume bullets and cover letter strictly sourced from candidate `confirmed_facts`, verified projects, and verified degrees.
  - `ClaimVerifier` extracts factual assertions and cross-references each token/metric against verified profile ground-truth.
  - If ungrounded assertions are detected (e.g., claiming unverified technologies or metrics), the engine triggers an automated repair loop (capped at 2 attempts per Section 5.2).
  - Produces an inspectable `ClaimAudit` trail for every generated sentence with atomic fact citations.

---

## 2. Terminal Commands Executed & Evidence

```bash
# Run docgen and claim verifier test suite
.venv/bin/pytest tests/unit/test_docgen_verifier.py -v
```

### Execution Output:
```text
tests/unit/test_docgen_verifier.py::test_grounded_generation_produces_zero_unsupported_claims PASSED [ 33%]
tests/unit/test_docgen_verifier.py::test_adversarial_hallucination_detected_and_repaired PASSED [ 66%]
tests/unit/test_docgen_verifier.py::test_claim_verifier_flags_unsupported_technical_skill PASSED [100%]

============================== 3 passed in 0.04s ===============================
VERDICT: PASS
```

---

## 3. How Other Teammates Can Call This Function

For **Samriddhi Raj** (in LangGraph `generate` and `approve` nodes) and **Sadiqua Parween** (in packet builder):
```python
from tools.docgen import generate_application_draft
from tools.schemas import Listing, Profile

# Generate fully audited draft
draft = generate_application_draft(listing, profile)

print(f"Draft Grounded: {draft.is_fully_grounded} (Unsupported Claims: {draft.unsupported_claim_count})")
for bullet in draft.tailored_resume_bullets:
    print(f"• {bullet}")

# Each claim can be inspected in UI for student review & approval:
for claim in draft.claims:
    print(f"[{claim.status.value.upper()}] {claim.claim_text} -> Note: {claim.audit_note}")
```
