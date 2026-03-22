from __future__ import annotations

import random
import numpy as np
from typing import List, Optional, Tuple

from .incident_type import IncidentType
from .incident import Incident


class IncidentSpawner:
    
    def __init__(
        self,
        base_probability: float = 0.01,
        severity_mean: float = 0.5,
        severity_std: float = 0.2,
        random_seed: Optional[int] = None
    ):
        self.base_probability = base_probability
        self.severity_mean = severity_mean
        self.severity_std = severity_std
        
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
    
    def should_spawn(
        self,
        element,
        element_type: str,
        current_time: int,
        active_incidents: List[Incident]
    ) -> Tuple[bool, Optional[IncidentType], float]:
        for inc in active_incidents:
            if inc.location_id == id(element) and inc.location_type == element_type:
                return False, None, 0.0
        
        probability = self.base_probability
        
        if element_type == "node":
            node_type = type(element).__name__
            if node_type == "ElecNode":
                probability *= 2.0
            elif node_type == "RiserNode":
                probability *= 1.5
            elif node_type == "TechNode":
                probability *= 1.3
        else:
            edge_type = type(element).__name__
            if edge_type == "FlowEdge":
                probability *= 1.2
        
        if random.random() > probability:
            return False, None, 0.0
        
        incident_type = self._select_incident_type(element, element_type)
        
        severity = np.clip(
            np.random.normal(self.severity_mean, self.severity_std),
            0.1, 1.0
        )
        
        return True, incident_type, severity
    
    def _select_incident_type(self, element, element_type: str) -> IncidentType:
        
        if element_type == "node":
            node_type = type(element).__name__
            
            if node_type == "ElecNode":
                return random.choices(
                    [IncidentType.POWER_OUTAGE, IncidentType.FIRE, IncidentType.SMOKE],
                    weights=[0.6, 0.3, 0.1]
                )[0]
                
            elif node_type == "RiserNode":
                return random.choices(
                    [IncidentType.FLOOD, IncidentType.GAS_LEAK, IncidentType.BLOCKAGE],
                    weights=[0.7, 0.2, 0.1]
                )[0]
                
            elif node_type == "ElevNode":
                return IncidentType.ELEVATOR_FAILURE
                
            elif node_type == "FlatNode":
                return random.choices(
                    list(IncidentType),
                    weights=[0.2, 0.25, 0.15, 0.05, 0.1, 0.1, 0.1, 0.05]
                )[0]
                
            else:
                return random.choice(list(IncidentType))
                
        else:
            edge_type = type(element).__name__
            if edge_type == "FlowEdge":
                return random.choices(
                    [IncidentType.BLOCKAGE, IncidentType.FLOOD, IncidentType.FIRE],
                    weights=[0.5, 0.3, 0.2]
                )[0]
            else:
                return random.choice(list(IncidentType))
