from __future__ import annotations

from typing import Optional
from dataclasses import dataclass

from .agent_action_type import AgentActionType


@dataclass
class AgentAction:
    action_type: AgentActionType
    target_id: Optional[int] = None
    target_type: Optional[str] = None  # node | edge

    def get_effectiveness(self) -> float:
        return self.action_type.effectiveness
