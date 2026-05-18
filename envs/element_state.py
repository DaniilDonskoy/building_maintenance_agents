from __future__ import annotations

from enum import Enum
from typing import Dict


class ElementState(Enum):
    IDLE = "idle"
    TEAM_DEPLOYED = "team_deployed"


class AgentStateMachine:

    def __init__(self, max_teams: int = 5):
        self.max_teams = max_teams
        self._states: Dict[int, ElementState] = {}

    @property
    def active_teams(self) -> int:
        return sum(1 for s in self._states.values() if s == ElementState.TEAM_DEPLOYED)

    def get_state(self, element_id: int) -> ElementState:
        return self._states.get(element_id, ElementState.IDLE)

    def has_team(self, element_id: int) -> bool:
        return self._states.get(element_id) == ElementState.TEAM_DEPLOYED

    def can_deploy(self, element_id: int) -> bool:
        return not self.has_team(element_id) and self.active_teams < self.max_teams

    def deploy(self, element_id: int) -> bool:
        if not self.can_deploy(element_id):
            return False
        self._states[element_id] = ElementState.TEAM_DEPLOYED
        return True

    def withdraw(self, element_id: int) -> bool:
        if not self.has_team(element_id):
            return False
        del self._states[element_id]
        return True

    def can_repair(self, element_id: int) -> bool:
        return self.has_team(element_id)

    def reset(self) -> None:
        self._states.clear()
