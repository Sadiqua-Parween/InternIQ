"""
Multi-Source Search Planner
Owner: Samriddhi Raj (Team HumanBot)
Status: Interface Stub
"""

from typing import List, Dict, Any
from tools.schemas import Preference


class SearchPlanner:
    def __init__(self):
        pass

    def create_plan(self, preference: Preference, attempt: int = 1) -> Dict[str, Any]:
        """
        Creates bounded search queries and source selections.
        If attempt > 1, relaxes constraints or explores fallback keywords.
        """
        keywords = preference.target_roles or ["Software Engineering Intern"]
        return {
            "attempt": attempt,
            "target_sources": ["manual_csv", "fixtures"],
            "query_keywords": keywords,
            "relaxed_mode": attempt > 1,
        }
