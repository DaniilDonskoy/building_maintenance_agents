from __future__ import annotations

from typing import Set
from enum import Enum

from incident_simulator import IncidentType


class AgentActionType(Enum):

    # REPAIR = 0                # Full repair (positive reward)
    # IGNORE = 1                # Ignoring (small penalty)
    # DEPLOY_TEAM = 2           # Send team (arrival)
    # WITHDRAW_TEAM = 3         # Withdraw team (departure)
    # TEMPORARY_FIX = 4         # Temporary patch (reduces but does not eliminate the problem)
    # SHUT_OFF_WATER = 5        # Shut off water in zone (isolation)
    # INSPECT = 6               # Inspection (information gathering)
    # MONITOR = 7               # Passive monitoring (zero cost)
    # CALL_BACKUP = 8           # Call backup (expensive)
    
    REPAIR = 0                # Full repair (positive reward)
    DEPLOY_TEAM = 1           # Send team (arrival)
    WITHDRAW_TEAM = 2         # Withdraw team (departure)
    SHUT_OFF_WATER = 3        # Shut off water in zone (isolation)
    INSPECT = 4               # Inspection (information gathering)
    MONITOR = 5               # Passive monitoring (zero cost)
    CALL_BACKUP = 6           # Call backup (expensive)

    @property
    def cost(self) -> float:
        mapping = {
            "REPAIR": 2.5,
            "DEPLOY_TEAM": 0.6,
            "WITHDRAW_TEAM": 0.0,
            "SHUT_OFF_WATER": 0.4,
            "INSPECT": 0.2,
            "MONITOR": 0.0,
            "CALL_BACKUP": 5.0,  # дорогое действие — не должно быть доминирующим
        }
        return mapping[self.name]

    @property
    def effectiveness(self) -> float:
        # in [0, 1]
        mapping = {
            "REPAIR": 0.8,
            # "IGNORE": 0.0,
            "DEPLOY_TEAM": 0.0,
            "WITHDRAW_TEAM": 0.0,
            # "TEMPORARY_FIX": 0.4,
            "SHUT_OFF_WATER": 0.7,
            "INSPECT": 0.0,
            "MONITOR": 0.0,
            "CALL_BACKUP": 0.8,
        }
        return mapping[self.name]

    @property
    def applicable_incident_types(self) -> Set[IncidentType]:
        all_incidents = set(IncidentType)
        specific = {
            "SHUT_OFF_WATER": all_incidents,
        }
        if self.name in {"REPAIR", "IGNORE", "DEPLOY_TEAM", "WITHDRAW_TEAM",
                         "TEMPORARY_FIX", "INSPECT",
                         "MONITOR", "CALL_BACKUP"}:
            return all_incidents
        return specific.get(self.name, set())