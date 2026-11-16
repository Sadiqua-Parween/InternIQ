# InternIQ: Sadiqua Parween — Work Completion Summary

**Team Member:** Sadiqua Parween  
**Team:** HumanBot (S-VYASA University × Newton School of Technology)  
**Assigned Ownership:** Data and Application Tools Engineer  
**Course:** Agentic AI (AI-IA)  
**Academic Year:** 2026  
**Instructors:** Venkata Gopal E | Mahfooz Ali  

---

## 1. Executive Summary

As assigned in the InternIQ Technical Report (Section 8.3) and Presentation (Page 7), I designed, implemented, and validated the complete **Data and Application Tools** subsystem for the InternIQ platform. 

This encompasses:
1. **Multi-Format Resume / Profile Parser (`tools/parser.py`)**: End-to-end extraction supporting PDF, DOCX, and raw text files. Generates fine-grained, atomic `EvidenceFact`s with document provenance for zero-hallucination downstream claim verification.
2. **Authorized Data Connectors & Ingestion Suite (`tools/fetchers/`)**: 
   - **Greenhouse Job Board API Connector (`tools/fetchers/greenhouse.py`)**: Public read-only GET connector with HTML cleaning, metadata extraction, and work mode detection.
   - **Lever Postings API Connector (`tools/fetchers/lever.py`)**: Public postings reader mapping site listings to canonical schema.
   - **User-Supplied URL Importer (`tools/fetchers/url_import.py`)**: Web reader with HTML text extraction and content hashing.
   - **Strict SSRF & URL Safety Guardrails (`tools/fetchers/url_safety.py`)**: Enforces HTTPS, blocks private IPs (RFC 1918), loopback, link-local, and cloud metadata endpoints (`169.254.169.254`).
   - **Listing Normalization & Deduplication (`tools/fetchers/__init__.py`)**: Cross-source deduplication via SHA-256 hashes and canonical URLs.
   - **CSV Ingestion Engine (`import_csv`)**: Structured batch ingestion from CSV files.
3. **Application Packet Builder (`tools/packet.py`)**: Assembles reviewable candidate packets with verified profile facts, grounded resume bullets, cover letters, and score breakdowns. Strictly enforces human-in-the-loop controls (no automated submission). Provides Markdown, JSON, and Plaintext export routines.
4. **Application Tracker & SQLite Persistence (`tools/tracker.py`)**: Relational SQLite storage implementing Table 6 of the report (`profiles`, `opportunities`, `drafts`, `tracker_events`, `feedback`, `audit_log`). Implements idempotency keys, human confirmation approval gates (FR-11), and DPDP/GDPR compliant full data deletion (Section 7.2).
5. **Comprehensive Unit Testing Suite**: Authored 19 new tests in `tests/unit/test_parser.py`, `tests/unit/test_fetchers.py`, `tests/unit/test_packet.py`, and `tests/unit/test_tracker.py`. **All 50/50 test cases now pass**.

---

## 2. Requirements Traceability Matrix

| Requirement ID & Topic | Report / Presentation Specification | Module Implemented | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **FR-02: Profile Parser** | Load resume data into an editable profile; preserve source evidence for extracted facts. | `tools/parser.py` | `tests/unit/test_parser.py`<br>**4/4 PASSED** |
| **FR-03: Multi-Source Retrieval** | Retrieve from authorized feeds/APIs (Greenhouse, Lever) + CSV/URL fallback. Read-only GET. | `tools/fetchers/greenhouse.py`<br>`tools/fetchers/lever.py`<br>`tools/fetchers/__init__.py` | `tests/unit/test_fetchers.py`<br>**6/6 PASSED** |
| **FR-04: Deduplication** | Normalize records and deduplicate using source IDs, canonical URLs, and content hash. | `tools/fetchers/__init__.py`<br>(`normalize_dedupe`) | `tests/unit/test_fetchers.py`<br>`test_scenario_deduplication_across_sources` |
| **FR-09: Application Packet** | Field-by-field packet for manual student review and copy-paste. | `tools/packet.py` | `tests/unit/test_packet.py`<br>**PASSED** |
| **FR-10: Tracker & Persistence** | Track saved/applied states, support editing, audit logging, and deletion. | `tools/tracker.py` | `tests/unit/test_tracker.py`<br>**6/6 PASSED** |
| **FR-11: Human Approval Gate** | Pause before any consequential state change; require explicit student confirmation. | `tools/tracker.py`<br>(`record_event`) | `test_tracker_event_confirmation_gate`<br>`test_scenario_tracker_human_approval_gate` |
| **Section 6.5 & Table 10: SSRF Defense** | Enforce HTTPS, reject private/loopback/cloud metadata IPs, bound payload sizes. | `tools/fetchers/url_safety.py` | `test_url_safety_scheme_validation`<br>`test_url_safety_ssrf_blocking` |
| **Section 7.2 & 10.3: DPDP Data Erasure** | Local storage, data minimization, user-triggered full data deletion. | `tools/tracker.py`<br>(`delete_all_user_data`) | `test_dpdp_full_deletion`<br>`test_scenario_data_deletion_lifecycle` |

---

## 3. Test & Verification Evidence

All 50 unit and scenario tests pass cleanly:

```bash
.venv/bin/pytest tests/ -v
```

```text
tests/scenarios/test_scenarios.py::test_scenario_clear_goal_end_to_end PASSED
tests/scenarios/test_scenarios.py::test_scenario_missing_deadline_preserved_as_unknown PASSED
tests/scenarios/test_scenarios.py::test_scenario_expired_deadline_disqualifies PASSED
tests/scenarios/test_scenarios.py::test_scenario_deduplication_across_sources PASSED
tests/scenarios/test_scenarios.py::test_scenario_fee_request_flagged_with_evidence PASSED
tests/scenarios/test_scenarios.py::test_scenario_prompt_injection_in_listing_sanitized PASSED
tests/scenarios/test_scenarios.py::test_scenario_tracker_human_approval_gate PASSED
tests/scenarios/test_scenarios.py::test_scenario_data_deletion_lifecycle PASSED
tests/scenarios/test_scenarios.py::test_scenario_execution_budget_circuit_breaker PASSED
tests/unit/test_docgen_verifier.py::test_grounded_generation_produces_zero_unsupported_claims PASSED
tests/unit/test_docgen_verifier.py::test_adversarial_hallucination_detected_and_repaired PASSED
tests/unit/test_docgen_verifier.py::test_claim_verifier_flags_unsupported_technical_skill PASSED
tests/unit/test_eligibility.py::test_eligible_candidate PASSED
tests/unit/test_eligibility.py::test_expired_deadline_disqualifies PASSED
tests/unit/test_eligibility.py::test_graduation_year_mismatch PASSED
tests/unit/test_eligibility.py::test_branch_mismatch PASSED
tests/unit/test_eligibility.py::test_min_gpa_failure PASSED
tests/unit/test_eligibility.py::test_unknown_when_profile_gpa_missing PASSED
tests/unit/test_eligibility.py::test_hard_work_mode_constraint PASSED
tests/unit/test_fetchers.py::test_url_safety_scheme_validation PASSED
tests/unit/test_fetchers.py::test_url_safety_ssrf_blocking PASSED
tests/unit/test_fetchers.py::test_strip_html_tags PASSED
tests/unit/test_fetchers.py::test_detect_work_mode PASSED
tests/unit/test_fetchers.py::test_greenhouse_connector_parsing PASSED
tests/unit/test_lever_connector_parsing PASSED
tests/unit/test_fetchers.py::test_deduplication PASSED
tests/unit/test_fetchers.py::test_import_csv PASSED
tests/unit/test_packet.py::test_build_application_packet PASSED
tests/unit/test_parser.py::test_text_resume_parsing PASSED
tests/unit/test_parser.py::test_synthetic_pdf_resume_parsing PASSED
tests/unit/test_parser.py::test_file_size_limit_rejection PASSED
tests/unit/test_parser.py::test_empty_content_graceful_fallback PASSED
tests/unit/test_ranker.py::test_skills_factor_calculation PASSED
tests/unit/test_ranker.py::test_skills_factor_empty_required_skills PASSED
tests/unit/test_ranker.py::test_preference_factor_evaluation PASSED
tests/unit/test_ranker.py::test_deadline_urgency_factor PASSED
tests/unit/test_ranker.py::test_weight_renormalization_missing_factors PASSED
tests/unit/test_ranker.py::test_ranking_sorts_descending PASSED
tests/unit/test_scam_check.py::test_clean_listing_no_flags PASSED
tests/unit/test_scam_check.py::test_fee_request_flagged PASSED
tests/unit/test_scam_check.py::test_free_email_domain_flagged PASSED
tests/unit/test_scam_check.py::test_implausible_urgency_flagged PASSED
tests/unit/test_scam_check.py::test_sensitive_info_request_flagged PASSED
tests/unit/test_scam_check.py::test_domain_mismatch_flagged PASSED
tests/unit/test_tracker.py::test_tracker_event_confirmation_gate PASSED
tests/unit/test_tracker.py::test_profile_persistence PASSED
tests/unit/test_tracker.py::test_opportunity_snapshot_persistence PASSED
tests/unit/test_tracker.py::test_draft_persistence PASSED
tests/unit/test_tracker.py::test_feedback_and_export PASSED
tests/unit/test_tracker.py::test_dpdp_full_deletion PASSED

============================== 50 passed in 6.98s ==============================
```
