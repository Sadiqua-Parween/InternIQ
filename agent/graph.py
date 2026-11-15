"""
LangGraph Agent Workflow and State Machine
Owner: Samriddhi Raj (Team HumanBot)
Status: Typed Run State and Workflow Skeleton

Coordinates the 9-stage bounded loop:
Perceive -> Plan -> Act -> Observe -> Vet -> Rank -> Generate -> Approve -> Record
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from tools.schemas import (
    Profile,
    Preference,
    Listing,
    EligibilityResult,
    RiskFlag,
    ScoreBreakdown,
    ApplicationDraft,
    Approval,
)
from agent.limits import ExecutionBudget


class InternIQAgentState(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile: Optional[Profile] = None
    preference: Optional[Preference] = None
    budget: ExecutionBudget = Field(default_factory=ExecutionBudget)
    
    # Discovery & Listings
    listings: List[Listing] = Field(default_factory=list)
    source_status: Dict[str, str] = Field(default_factory=dict)
    
    # Vetting & Ranking (Mohd Faizan Khan's components)
    eligibility_map: Dict[str, EligibilityResult] = Field(default_factory=dict)
    risk_map: Dict[str, List[RiskFlag]] = Field(default_factory=dict)
    scores_map: Dict[str, ScoreBreakdown] = Field(default_factory=dict)
    ranked_listing_ids: List[str] = Field(default_factory=list)
    
    # Generation & Approval
    drafts_map: Dict[str, ApplicationDraft] = Field(default_factory=dict)
    approval: Optional[Approval] = None
    errors: List[str] = Field(default_factory=list)
    completion_status: str = "in_progress"
