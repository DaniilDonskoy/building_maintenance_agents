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

    def _key(self, building_idx: int, element_id: int) -> int:
        return (building_idx << 32) | element_id

    @property
    def active_teams(self) -> int:
        return sum(1 for s in self._states.values() if s == ElementState.TEAM_DEPLOYED)

    def has_team(self, building_idx: int, element_id: int) -> bool:
        return self._states.get(self._key(building_idx, element_id)) == ElementState.TEAM_DEPLOYED

    def can_deploy(self, building_idx: int, element_id: int) -> bool:
        return not self.has_team(building_idx, element_id) and self.active_teams < self.max_teams

    def deploy(self, building_idx: int, element_id: int) -> bool:
        if not self.can_deploy(building_idx, element_id):
            return False
        self._states[self._key(building_idx, element_id)
                     ] = ElementState.TEAM_DEPLOYED
        return True

    def withdraw(self, building_idx: int, element_id: int) -> bool:
        if not self.has_team(building_idx, element_id):
            return False
        del self._states[self._key(building_idx, element_id)]
        return True

    def can_repair(self, building_idx: int, element_id: int) -> bool:
        return self.has_team(building_idx, element_id)

    def reset(self) -> None:
        self._states.clear()
