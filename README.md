# InternIQ: Agentic Internship Assistant

> **Agentic AI Internship Discovery, Eligibility Verification, Ranking, and Application Preparation Assistant**
> *Team HumanBot — S-VYASA University × Newton School of Technology*

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Framework](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Validation](https://img.shields.io/badge/validation-Pydantic%20v2-green.svg)](https://docs.pydantic.dev/)
[![Embeddings](https://img.shields.io/badge/embeddings-all--MiniLM--L6--v2-purple.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 👥 Team HumanBot Responsibilities

| Team Member | Domain & Modules | Key Ownership |
| :--- | :--- | :--- |
| **Mohd Faizan Khan** | **Evaluation & Verification** | **Deterministic Eligibility Engine** (`tools/eligibility.py`), **Transparent Hybrid Ranker** (`tools/ranker.py`), **Scam-Signal Detection** (`tools/scam_check.py`), **Document Generation & Claim Verifier** (`tools/docgen.py`, `agent/verifier.py`), **Evaluation Benchmarks & Scripts** (`eval/`, `tests/`) |
| **Samriddhi Raj** | **Agent Core & Interface** | LangGraph core workflow (`agent/graph.py`), Multi-source search planner (`agent/planner.py`), Execution limits & safety circuit breakers (`agent/limits.py`), Memory management (`agent/memory.py`), Streamlit UI (`app/ui.py`) |
| **Sadiqua Parween** | **Data & Application Tools** | Authorized source fetchers & connectors (`tools/fetchers/`), Resume/profile parser (`tools/parser.py`), Listing normalization & deduplication, Application packet builder (`tools/packet.py`), SQLite tracker (`tools/tracker.py`) |

---

## 🏗️ Repository Architecture

```
InternIQ/
├── app/
│   ├── ui.py               # Streamlit web application
│   └── cli.py              # CLI evaluation and runner
├── agent/
│   ├── graph.py            # LangGraph state machine & 9-stage loop
│   ├── planner.py          # Search query & source planner
│   ├── verifier.py         # Claim-level audit & zero-hallucination verifier
│   ├── memory.py           # Profile, episodic & run working state
│   └── limits.py           # Per-run execution caps & circuit breakers
├── tools/
│   ├── schemas.py          # Strongly-typed Pydantic v2 schemas
│   ├── eligibility.py      # Hard constraint deterministic eligibility engine
│   ├── ranker.py           # Hybrid ranker (Skills, Semantic, Preference, Deadline)
│   ├── scam_check.py       # Heuristic scam-signal detection engine
│   ├── docgen.py           # Grounded resume bullets & cover letter generator
│   ├── parser.py           # Profile and resume extraction
│   ├── fetchers/           # Authorized feed connectors & CSV importer
│   ├── packet.py           # Field-by-field student review packet builder
│   └── tracker.py          # SQLite local persistence & audit logging
├── eval/
│   ├── labelled_listings.csv   # Benchmark dataset (40+ labelled opportunities)
│   ├── run_eval.py             # Evaluation harness (Precision@10, Confusion Matrix)
│   └── results/                # Evaluation reports and metric dumps
├── tests/
│   ├── unit/               # Deterministic unit test suite
│   └── scenarios/          # End-to-end failure injection and recovery tests
├── docs/                   # Implementation notes and sync documentation
├── config.example.env      # Example environment configuration
├── requirements.txt        # Python dependency manifest
└── pyproject.toml          # Project metadata & configuration
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- `uv` (recommended) or standard `venv` + `pip`
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone the repository
git clone https://github.com/Faizan-902/InternIQ.git
cd InternIQ

# Using uv (fastest)
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# Or using standard venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Verification Tests
```bash
pytest tests/ -v
```

### 4. Run Evaluation Suite
```bash
python -m eval.run_eval
```
