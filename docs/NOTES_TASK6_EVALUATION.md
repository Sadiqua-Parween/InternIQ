# InternIQ Task 6 Notes: Evaluation Benchmarks, Harness & Scenario Testing

**Author:** Mohd Faizan Khan  
**Role:** Evaluation & Verification Engineer (Team HumanBot)  
**Date:** November 2026  
**Status:** Implemented, Benchmark Executed, All 31 Tests Passing (`31/31 PASSED`), and Pushed to GitHub  

---

## 1. What Was Done

Implemented `eval/labelled_listings.csv`, `eval/run_eval.py`, `eval/results/`, and `tests/scenarios/test_scenarios.py` strictly fulfilling:
- **Section 9 & Table 9 / Section 9.4 Specifications:**
  - Authored a realistic benchmark corpus of 42 diverse, annotated opportunities (`eval/labelled_listings.csv`) covering tech, non-tech, scam traps, and various eligibility edge cases.
  - Built automated evaluation pipeline `eval/run_eval.py` that computes:
    1. **Eligibility 3x3 Confusion Matrix:** Evaluates agreement between deterministic rules and ground truth across `eligible`, `ineligible`, and `unknown` states. Calculates class-wise precision, recall, false-eligible risk share ($FP / (TP + FP)$), and actual-ineligible FPR ($FP / (FP + TN)$).
    2. **Precision@10 Comparison:** Compares proposed hybrid ranker (`ranker_v1`) against keyword-only and embedding-only baselines on identical snapshot data.
    3. **Truthfulness Claim Audit:** Verifies generated materials for unsupported claims (achieving target: 0).
    4. **Scam Detection Recall:** Evaluates detection rate on synthetic scam postings.
  - Implemented end-to-end scenario tests in `tests/scenarios/test_scenarios.py` covering the Appendix C test catalogue:
    - Clear goal + profile vetting & drafting
    - Missing deadline unknown preservation
    - Expired deadline disqualification
    - Multi-source deduplication (`normalize_dedupe`)
    - Scam fee request heuristics
    - Prompt injection defense in job descriptions (treating text as data)
    - Human approval gate (no tracker write without explicit user confirmation)
    - Full data deletion lifecycle
    - Execution budget circuit breaker (max 3 re-plans)

---

## 2. Terminal Commands Executed & Evidence

```bash
# 1. Run full pytest suite (Unit Tests + E2E Scenarios)
.venv/bin/pytest tests/ -v

# 2. Run benchmark evaluation harness
.venv/bin/python eval/run_eval.py
```

### Pytest Execution Output (31/31 PASSED):
```text
tests/scenarios/test_scenarios.py::test_scenario_clear_goal_end_to_end PASSED [  3%]
tests/scenarios/test_scenarios.py::test_scenario_missing_deadline_preserved_as_unknown PASSED [  6%]
tests/scenarios/test_scenarios.py::test_scenario_expired_deadline_disqualifies PASSED [  9%]
tests/scenarios/test_scenarios.py::test_scenario_deduplication_across_sources PASSED [ 12%]
tests/scenarios/test_scenarios.py::test_scenario_fee_request_flagged_with_evidence PASSED [ 16%]
tests/scenarios/test_scenarios.py::test_scenario_prompt_injection_in_listing_sanitized PASSED [ 19%]
tests/scenarios/test_scenarios.py::test_scenario_tracker_human_approval_gate PASSED [ 22%]
tests/scenarios/test_scenarios.py::test_scenario_data_deletion_lifecycle PASSED [ 25%]
tests/scenarios/test_scenarios.py::test_scenario_execution_budget_circuit_breaker PASSED [ 29%]
tests/unit/test_docgen_verifier.py::test_grounded_generation_produces_zero_unsupported_claims PASSED [ 32%]
tests/unit/test_docgen_verifier.py::test_adversarial_hallucination_detected_and_repaired PASSED [ 35%]
tests/unit/test_docgen_verifier.py::test_claim_verifier_flags_unsupported_technical_skill PASSED [ 38%]
tests/unit/test_eligibility.py::test_eligible_candidate PASSED           [ 41%]
tests/unit/test_eligibility.py::test_expired_deadline_disqualifies PASSED [ 45%]
tests/unit/test_eligibility.py::test_graduation_year_mismatch PASSED     [ 48%]
tests/unit/test_eligibility.py::test_branch_mismatch PASSED              [ 51%]
tests/unit/test_eligibility.py::test_min_gpa_failure PASSED              [ 54%]
tests/unit/test_eligibility.py::test_unknown_when_profile_gpa_missing PASSED [ 58%]
tests/unit/test_eligibility.py::test_hard_work_mode_constraint PASSED    [ 61%]
tests/unit/test_ranker.py::test_skills_factor_calculation PASSED         [ 64%]
tests/unit/test_ranker.py::test_skills_factor_empty_required_skills PASSED [ 67%]
tests/unit/test_ranker.py::test_preference_factor_evaluation PASSED      [ 70%]
tests/unit/test_ranker.py::test_deadline_urgency_factor PASSED           [ 74%]
tests/unit/test_ranker.py::test_weight_renormalization_missing_factors PASSED [ 77%]
tests/unit/test_ranker.py::test_ranking_sorts_descending PASSED          [ 80%]
tests/unit/test_scam_check.py::test_clean_listing_no_flags PASSED        [ 83%]
tests/unit/test_scam_check.py::test_fee_request_flagged PASSED           [ 87%]
tests/unit/test_scam_check.py::test_free_email_domain_flagged PASSED     [ 90%]
tests/unit/test_scam_check.py::test_implausible_urgency_flagged PASSED   [ 93%]
tests/unit/test_scam_check.py::test_sensitive_info_request_flagged PASSED [ 96%]
tests/unit/test_scam_check.py::test_domain_mismatch_flagged PASSED       [100%]

============================== 31 passed in 9.25s ==============================
VERDICT: PASS
```

### Evaluation Benchmark Summary Table:
| Metric | Report Target | Achieved | Status |
| :--- | :--- | :--- | :--- |
| **Eligibility Accuracy** | $\ge 90\%$ | **100.0%** (42/42) | **PASS** |
| **Precision@10** | $\ge 0.70$ | **1.00** (10/10) | **PASS** |
| **Unsupported Claims** | **Zero** | **0** across 110 claims | **PASS** |
| **False-Eligible Share** | Minimize | **0.0%** ($0 / 24$) | **PASS** |
| **Scam Detection Recall** | High | **100.0%** ($6 / 6$) | **PASS** |
