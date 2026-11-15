# InternIQ Task 4 Notes: Hybrid Matching & Transparent Ranking Engine

**Author:** Mohd Faizan Khan  
**Role:** Evaluation & Verification Engineer (Team HumanBot)  
**Date:** November 2026  
**Status:** Implemented, Tested (`6/6 PASSED`), and Pushed to GitHub  

---

## 1. What Was Done

Implemented `tools/ranker.py` and unit tests in `tests/unit/test_ranker.py` fulfilling:
- **Functional Requirement FR-06:** Rank using a readable score breakdown and skill-gap explanation.
- **Section 7.3 & Table 7 Formula Implementation:**
  - Integrated 4-factor hybrid weighted model:
    $$\text{Score} = \frac{\sum_{i \in \text{available}} w_i \cdot f_i}{\sum_{i \in \text{available}} w_i}$$
    with baseline weights:
    - **Skills Match ($w_1 = 0.35$):** Required skills match fraction; provides explicit list of matched skills, missing required skills, and evidence coverage.
    - **Semantic Fit ($w_2 = 0.35$):** High-dimensional embeddings computed using Hugging Face `sentence-transformers/all-MiniLM-L6-v2` with linear mapping $[-1, 1] \to [0, 1]$ clipped (plus fast deterministic TF-IDF fallback for offline/isolated execution).
    - **Preference Fit ($w_3 = 0.20$):** Soft preferences (roles, domains, locations, work modes, stipend) evaluated against assessable listing fields.
    - **Deadline Urgency ($w_4 = 0.10$):** Linear urgency factor $D = 1 - \min(\text{days\_remaining} / 30, 1)$ for open roles.
  - **Missing Factor Renormalization:** If a factor is missing (e.g. listing does not specify deadline or required skills), that factor is excluded from both numerator and denominator, and weights are dynamically renormalized to sum to $1.00$.
  - **No Artificial Zeros:** If no usable factors exist, the score is returned as `None` (review-only).

---

## 2. Terminal Commands Executed & Evidence

```bash
# Run ranker unit test suite
.venv/bin/pytest tests/unit/test_ranker.py -v
```

### Execution Output:
```text
tests/unit/test_ranker.py::test_skills_factor_calculation PASSED         [ 16%]
tests/unit/test_ranker.py::test_skills_factor_empty_required_skills PASSED [ 33%]
tests/unit/test_ranker.py::test_preference_factor_evaluation PASSED      [ 50%]
tests/unit/test_ranker.py::test_deadline_urgency_factor PASSED           [ 66%]
tests/unit/test_ranker.py::test_weight_renormalization_missing_factors PASSED [ 83%]
tests/unit/test_ranker.py::test_ranking_sorts_descending PASSED          [100%]

============================== 6 passed in 9.89s ===============================
VERDICT: PASS
```

---

## 3. How Other Teammates Can Call This Function

For **Samriddhi Raj** (in LangGraph `rank` node) and **Streamlit UI**:
```python
from tools.ranker import score_opportunity, rank_opportunities
from tools.schemas import Listing, Profile, Preference

# Score single listing with full transparency breakdown
score_breakdown = score_opportunity(listing, profile, preference)
print(f"Total Score: {score_breakdown.total_score}")
print(f"Missing Skills: {score_breakdown.missing_skills}")
for step in score_breakdown.explanations:
    print(f"  - {step}")

# Or rank a list of opportunities descending by score
ranked_list = rank_opportunities(all_listings, profile, preference)
for listing, breakdown in ranked_list:
    print(f"[{breakdown.total_score:.3f}] {listing.title} at {listing.organization}")
```
