from __future__ import annotations

from typing import Optional
from dataclasses import dataclass

from .agent_action_type import AgentActionType


@dataclass
class AgentAction:
    action_type: AgentActionType
    target_id: Optional[int] = None
    target_type: Optional[str] = None  # node | edge
    resource_multiplier: float = 1.0
    
    def get_cost(self) -> float:
        return self.action_type.cost * self.resource_multiplier
    
    def get_effectiveness(self) -> float:
        return self.action_type.effectiveness * self.resource_multiplier
