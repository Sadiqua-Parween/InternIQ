# InternIQ Task 1 Notes: Repository Initialization & Shared Architecture

**Author:** Mohd Faizan Khan  
**Role:** Evaluation & Verification Engineer (Team HumanBot)  
**Date:** November 2026  
**Status:** Completed & Pushed to GitHub  

---

## 1. What Was Done

1. **Local & Remote Repository Setup:**
   - Initialized a Git version-controlled repository with default branch `main`.
   - Connected with GitHub via `gh` CLI as user `Faizan-902` and created public repository:  
     `https://github.com/Faizan-902/InternIQ`
   - Configured `.gitignore` to prevent committing virtual environments, cache files, database artifacts, and secrets.

2. **Environment & Dependency Manifest:**
   - Created Python 3.11 isolated virtual environment (`.venv`) using `uv`.
   - Authored `requirements.txt` and `pyproject.toml` including:
     - Data validation: `pydantic>=2.6.0`
     - ML / Semantic Search: `sentence-transformers>=2.5.0`, `torch`, `scikit-learn`, `numpy`
     - Network & Parsing: `httpx>=0.27.0`, `pypdf`, `python-docx`
     - UI & Display: `streamlit`, `rich`, `tabulate`
     - Orchestration: `langgraph`, `langchain-core`
     - Testing: `pytest>=8.0.0`, `pytest-cov`, `ruff`
   - Configured `config.example.env` matching Table 10 and Section 10.6 execution limits.

3. **Shared Strongly-Typed Schemas (`tools/schemas.py`):**
   - Implemented complete Pydantic V2 models conforming to Appendix B and Tables 5 & 6 of the project report:
     - `Profile`, `Education`, `Skill`, `Project`, `EvidenceFact`
     - `Preference`, `Listing`, `WorkMode`
     - `EligibilityResult`, `EligibilityVerdict`
     - `RiskFlag`, `RiskSeverity`, `ScamCheckResult`
     - `ScoreBreakdown` (with 4-factor hybrid schema)
     - `ClaimAudit`, `ClaimStatus`, `ApplicationDraft`
     - `Approval`, `UserDecision`, `TrackerEvent`

4. **Teammate Integration Stubs (Zero-Conflict Contract):**
   - Because no other teammate has started yet, we designed modular interface contracts so when teammates clone the repository, their components plug in without conflicts:
     - For **Samriddhi Raj**: Created `agent/graph.py`, `agent/planner.py`, `agent/limits.py`, `agent/memory.py`, and `app/ui.py`.
     - For **Sadiqua Parween**: Created `tools/parser.py`, `tools/fetchers/__init__.py`, `tools/packet.py`, and `tools/tracker.py`.

---

## 2. Terminal Commands Executed & Explanations

| Command | Purpose | Explanation |
| :--- | :--- | :--- |
| `uv venv .venv --python 3.11` | Environment creation | Uses `uv` to download and initialize Python 3.11.15 in `.venv`. |
| `git init && git branch -M main` | Git initialization | Sets up local git tracking with `main` as default branch. |
| `gh repo create InternIQ --public --source=. --remote=origin` | GitHub repository creation | Creates GitHub repo `Faizan-902/InternIQ` and binds `origin` remote. |
| `uv pip install -r requirements.txt --python .venv/bin/python` | Dependency installation | Ultra-fast parallel installation of 99 dependencies in 1m 39s. |
| `git add . && git commit -m "..." && git push -u origin main` | Remote sync | Commits initial architecture and pushes to GitHub. |

---

## 3. How This Protects Teammate Work (Conflict Prevention)

- **Isolated File Ownership:** Each teammate has their own dedicated files. Faizan works on `tools/eligibility.py`, `tools/ranker.py`, `tools/scam_check.py`, `tools/docgen.py`, `agent/verifier.py`, and `eval/`.
- **Shared Schemas Authority:** All data models are centralized in `tools/schemas.py`. Teammates import models from here, guaranteeing type compatibility across parser, ranker, LangGraph state, and UI.
