"""
Three-Layer Agent Memory Architecture
Owner: Samriddhi Raj (Team HumanBot)
Status: Memory Manager Implementation

Implements Section 7.1:
1. Profile Memory: Parsed education, skills, projects with provenance
2. Episodic Memory: Search constraints, saved roles, user feedback
3. Run Working State: Short-lived intermediate plan and observations
"""

from typing import Dict, Any, List, Optional
from tools.schemas import Profile, Preference, Listing


class AgentMemoryManager:
    def __init__(self):
        self.profile_memory: Optional[Profile] = None
        self.preference_memory: Optional[Preference] = None
        self.episodic_history: List[Dict[str, Any]] = []
        self.run_scratchpad: Dict[str, Any] = {}

    def set_profile(self, profile: Profile) -> None:
        self.profile_memory = profile

    def set_preference(self, preference: Preference) -> None:
        self.preference_memory = preference

    def record_episode(self, episode: Dict[str, Any]) -> None:
        self.episodic_history.append(episode)

    def clear_run_state(self) -> None:
        self.run_scratchpad.clear()
