"""
Agent Execution Limits and Safety Circuit Breakers
Owner: Samriddhi Raj (Team HumanBot)
Status: Safety Limits Implementation

Enforces Table 10 & Section 10.6 execution bounds:
- Max 3 search / re-plan rounds
- Max tool calls per run
- Timeout limits
"""

from pydantic import BaseModel, Field


class ExecutionBudget(BaseModel):
    max_replan_rounds: int = Field(3, description="Hard cap on re-planning loops")
    max_tool_calls: int = Field(15, description="Maximum tool calls per user run")
    max_generation_attempts: int = Field(2, description="Claim-verifier retry cap")
    timeout_seconds: int = Field(30, description="Per-step timeout limit")
    
    current_replan_count: int = 0
    current_tool_calls: int = 0
    current_gen_attempts: int = 0

    def can_replan(self) -> bool:
        return self.current_replan_count < self.max_replan_rounds

    def record_replan(self) -> None:
        self.current_replan_count += 1
        if self.current_replan_count > self.max_replan_rounds:
            raise RuntimeError(f"Circuit Breaker: Re-plan limit of {self.max_replan_rounds} exceeded.")

    def record_tool_call(self) -> None:
        self.current_tool_calls += 1
        if self.current_tool_calls > self.max_tool_calls:
            raise RuntimeError(f"Circuit Breaker: Tool call limit of {self.max_tool_calls} exceeded.")
