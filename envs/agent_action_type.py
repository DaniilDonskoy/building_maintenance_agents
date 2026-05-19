from __future__ import annotations

from typing import Set
from enum import Enum

from incident_simulator import IncidentType


class AgentActionType(Enum):
    REPAIR = 0
    DEPLOY_TEAM = 1
    WITHDRAW_TEAM = 2
    SHUT_OFF_WATER = 3
    INSPECT = 4
    MONITOR = 5

    @property
    def effectiveness(self) -> float:
        mapping = {
            "REPAIR": 0.8,
            "DEPLOY_TEAM": 0.0,
            "WITHDRAW_TEAM": 0.0,
            "SHUT_OFF_WATER": 0.7,
            "INSPECT": 0.0,
            "MONITOR": 0.0,
        }
        return mapping[self.name]

    @property
    def applicable_incident_types(self) -> Set[IncidentType]:
        all_incidents = set(IncidentType)
        specific = {
            "SHUT_OFF_WATER": all_incidents,
        }
        if self.name in {"REPAIR", "DEPLOY_TEAM", "WITHDRAW_TEAM", "SHUT_OFF_WATER", "INSPECT", "MONITOR"}:
            return all_incidents
        return specific.get(self.name, set())
