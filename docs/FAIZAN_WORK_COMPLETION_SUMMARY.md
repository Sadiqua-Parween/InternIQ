# InternIQ: Mohd Faizan Khan — Work Completion Summary

**Team Member:** Mohd Faizan Khan  
**Team:** HumanBot (S-VYASA University × Newton School of Technology)  
**Assigned Ownership:** Evaluation & Verification Engineer  
**Modules Delivered:**
1. Deterministic Eligibility Engine (`tools/eligibility.py`)
2. Heuristic Scam-Signal Detection Engine (`tools/scam_check.py`)
3. Hybrid Matching & Transparent Ranking Engine (`tools/ranker.py`)
4. Grounded Document Generation & Claim-Level Verifier (`tools/docgen.py`, `agent/verifier.py`)
5. Evaluation Dataset & Benchmark Harness (`eval/labelled_listings.csv`, `eval/run_eval.py`, `eval/results/`)
6. Unit & End-to-End Scenario Test Suite (`tests/unit/`, `tests/scenarios/` — **31/31 PASSED**)
7. Shared Pydantic V2 Schemas & Zero-Conflict Teammate Stubs (`tools/schemas.py`, `tools/parser.py`, `tools/fetchers/`, `tools/packet.py`, `tools/tracker.py`, `agent/graph.py`, `agent/planner.py`, `agent/limits.py`, `agent/memory.py`, `app/ui.py`)

---

## 1. Traceability Matrix: How Requirements Were Met

| Specification in Report / Presentation | Module Implemented | Evidence / Verification |
| :--- | :--- | :--- |
| **FR-05: Deterministic Eligibility**<br>Check hard constraints, preserve unknown states, evaluate expired deadlines | `tools/eligibility.py` | `tests/unit/test_eligibility.py`<br>**7/7 PASSED** |
| **FR-07: Scam-Signal Detection**<br>Flag fee requests, unverified emails, domain mismatches, urgency without categorical fraud accusations | `tools/scam_check.py` | `tests/unit/test_scam_check.py`<br>**6/6 PASSED** (100% recall) |
| **FR-06 & Table 7: Hybrid Transparent Ranker**<br>Skills (0.35), Semantic (0.35 MiniLM), Preference (0.20), Deadline (0.10) with weight renormalization | `tools/ranker.py` | `tests/unit/test_ranker.py`<br>**6/6 PASSED** |
| **FR-08: Grounded Generation & Claim Audit**<br>Tailored bullets & cover letter from verified facts; zero unsupported claims | `tools/docgen.py`<br>`agent/verifier.py` | `tests/unit/test_docgen_verifier.py`<br>**3/3 PASSED** (0 ungrounded) |
| **Section 9 & Table 9: Evaluation Benchmark**<br>42-listing labelled corpus, 3x3 confusion matrix, Precision@10 vs baselines | `eval/labelled_listings.csv`<br>`eval/run_eval.py` | `eval/results/summary_metrics.json`<br>**100% Accuracy, P@10 = 1.00** |
| **Appendix C: Scenario Testing Catalogue**<br>E2E pipeline, deduplication, prompt injection defense, approval gate, DPDP deletion | `tests/scenarios/test_scenarios.py` | `tests/scenarios/`<br>**9/9 PASSED** |

---

## 2. Command Reference & How to Run Everything

### A. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Faizan-902/InternIQ.git
cd InternIQ

# Create Python 3.11 environment using uv
uv venv .venv --python 3.11
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### B. Run Test Suite
```bash
# Run all 31 unit and scenario tests
.venv/bin/pytest tests/ -v
```

### C. Run Evaluation Benchmark
```bash
# Run the 42-opportunity evaluation harness
.venv/bin/python eval/run_eval.py
```

---

## 3. Guide for Teammates (Syncing Without Conflicts)

Because no other teammate had started yet, the architecture was intentionally modularized so that each team member has isolated files and clear contracts:

### A. For Samriddhi Raj (Agent Core & Interface)
- **Your Files to Work On:**
  - `agent/graph.py`: LangGraph state machine wiring nodes (`perceive`, `plan`, `act`, `observe`, `vet`, `rank`, `generate`, `approve`, `record`).
  - `agent/planner.py`: Multi-source search query planner.
  - `agent/limits.py`: Circuit breakers and execution budgets (already has budget class).
  - `agent/memory.py`: Profile, episodic, and run state manager.
  - `app/ui.py`: Streamlit frontend interface.
- **How to Call Faizan's Modules:**
  - In `vet` node: Call `check_eligibility(listing, profile)` and `check_scam_signals(listing)`.
  - In `rank` node: Call `rank_opportunities(listings, profile, preference)`.
  - In `generate` node: Call `generate_application_draft(listing, profile)`.
  - All input/output models are in `tools/schemas.py`.

### B. For Sadiqua Parween (Data & Application Tools)
- **Your Files to Work On:**
  - `tools/fetchers/`: Implement live connectors for Greenhouse and Lever APIs, plus CSV import.
  - `tools/parser.py`: Implement PDF and DOCX parsing using `pypdf` / `python-docx`.
  - `tools/packet.py`: Build student-reviewable packet dictionary.
  - `tools/tracker.py`: SQLite persistence and application event tracking (working baseline already provided!).
- **How to Call Faizan's Modules:**
  - In normalization: Call `normalize_dedupe(listings)` from `tools/fetchers/`.
  - When feeding listings into the system, instantiate `Listing` models from `tools/schemas.py`.
