from __future__ import annotations

from typing import Set
from enum import Enum

from .incident_simulator import IncidentType


class AgentActionType(Enum):
    DEPLOY_FIREFIGHTERS = 0
    DEPLOY_PLUMBERS = 1
    DEPLOY_ELECTRICIANS = 2
    DEPLOY_ELEVATOR_TECH = 3
    DEPLOY_GENERAL_TEAM = 4
    EVACUATE_ZONE = 5
    ISOLATE_ZONE = 6
    INSPECT_ELEMENT = 7
    REPAIR_ELEMENT = 8
    CALL_BACKUP = 9
    MONITOR = 10
    DEPLOY_HAZMAT = 11
    STRUCTURAL_SUPPORT = 12
    
    @property
    def cost(self) -> float:
        costs = {
            "DEPLOY_FIREFIGHTERS": 2.0,
            "DEPLOY_PLUMBERS": 1.5,
            "DEPLOY_ELECTRICIANS": 1.5,
            "DEPLOY_ELEVATOR_TECH": 1.0,
            "DEPLOY_GENERAL_TEAM": 1.0,
            "EVACUATE_ZONE": 0.5,
            "ISOLATE_ZONE": 0.3,
            "INSPECT_ELEMENT": 0.1,
            "REPAIR_ELEMENT": 2.0,
            "CALL_BACKUP": 5.0,
            "MONITOR": 0.0,
            "DEPLOY_HAZMAT": 3.0,
            "STRUCTURAL_SUPPORT": 4.0
        }
        return costs[self.name]
    
    @property
    def effectiveness(self) -> float:
        effectiveness = {
            "DEPLOY_FIREFIGHTERS": 0.4,
            "DEPLOY_PLUMBERS": 0.35,
            "DEPLOY_ELECTRICIANS": 0.45,
            "DEPLOY_ELEVATOR_TECH": 0.5,
            "DEPLOY_GENERAL_TEAM": 0.2,
            "EVACUATE_ZONE": 0.0,
            "ISOLATE_ZONE": 0.0,
            "INSPECT_ELEMENT": 0.0,
            "REPAIR_ELEMENT": 0.3,
            "CALL_BACKUP": 0.0,
            "MONITOR": 0.0,
            "DEPLOY_HAZMAT": 0.5,
            "STRUCTURAL_SUPPORT": 0.6
        }
        return effectiveness[self.name]
    
    @property
    def applicable_incident_types(self) -> Set[IncidentType]:
        mapping = {
            "DEPLOY_FIREFIGHTERS": {IncidentType.FIRE, IncidentType.SMOKE},
            "DEPLOY_PLUMBERS": {IncidentType.FLOOD, IncidentType.GAS_LEAK},
            "DEPLOY_ELECTRICIANS": {IncidentType.POWER_OUTAGE},
            "DEPLOY_ELEVATOR_TECH": {IncidentType.ELEVATOR_FAILURE},
            "DEPLOY_GENERAL_TEAM": {
                IncidentType.BLOCKAGE, IncidentType.STRUCTURAL_DAMAGE
            },
            "REPAIR_ELEMENT": {
                IncidentType.BLOCKAGE, IncidentType.STRUCTURAL_DAMAGE,
                IncidentType.FLOOD, IncidentType.GAS_LEAK
            },
            "DEPLOY_HAZMAT": {IncidentType.GAS_LEAK},
            "STRUCTURAL_SUPPORT": {IncidentType.STRUCTURAL_DAMAGE}
        }
        return mapping.get(self.name, set())
