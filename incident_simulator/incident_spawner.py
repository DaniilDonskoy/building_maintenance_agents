from __future__ import annotations

import random
import numpy as np
from typing import Any, List, Optional, Tuple

from .incident_type import IncidentType
from .incident import Incident


class IncidentSpawner:
    
    def __init__(
        self,
        base_probability: float = 1.0,
        severity_mean: float = 0.5,
        severity_std: float = 0.2,
        random_seed: Optional[int] = None,
        incident_probabilities: dict[str | IncidentType, float] | None = None,
    ):
        self.base_probability = base_probability
        self.severity_mean = severity_mean
        self.severity_std = severity_std
        self.incident_probabilities = {
            self._incident_type_key(incident_type): probability
            for incident_type, probability in (incident_probabilities or {}).items()
        }
        
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
        
        incident_type = self._select_incident_type(element, element_type)
        if incident_type is None:
            return False, None, 0.0
        
        type_probability = self.incident_probabilities.get(
            incident_type.value,
            incident_type.base_probability,
        )
        probability = type_probability * self.base_probability
        
        if random.random() > probability:
            return False, None, 0.0
        
        severity = np.clip(
            np.random.normal(self.severity_mean, self.severity_std),
            0.1, 1.0
        )
        
        return True, incident_type, severity

    def _incident_type_key(self, incident_type: Any) -> str:
        if isinstance(incident_type, IncidentType):
            return incident_type.value
        return str(incident_type)
    
    def _select_incident_type(self, element, element_type: str) -> Optional[IncidentType]:
        water_system = self._get_water_system(element)
        
        if element_type == "node":
            node_type = type(element).__name__
            
            if node_type not in {"RiserNode", "TechNode"}:
                return None
            
            if water_system == "gvs":
                return IncidentType.GVS_RISER_FAILURE
            if water_system == "hvs":
                return IncidentType.HVS_RISER_FAILURE
            return random.choice([
                IncidentType.GVS_RISER_FAILURE,
                IncidentType.HVS_RISER_FAILURE,
            ])
                
        else:
            edge_type = type(element).__name__
            if edge_type != "FlowEdge":
                return None
            
            if water_system == "gvs":
                return IncidentType.GVS_PIPE_FAILURE
            if water_system == "hvs":
                return IncidentType.HVS_PIPE_FAILURE
            return random.choice([
                IncidentType.GVS_PIPE_FAILURE,
                IncidentType.HVS_PIPE_FAILURE,
            ])
    
    def _get_water_system(self, element) -> Optional[str]:
        features = getattr(element, "features", {}) or {}
        raw_value = (
            features.get("water_system")
            or features.get("system")
            or features.get("utility")
        )
        if raw_value is None:
            return None
        
        value = str(raw_value).lower()
        if value in {"gvs", "hot_water", "hot", "dhw", "гвс"}:
            return "gvs"
        if value in {"hvs", "cold_water", "cold", "cws", "хвс"}:
            return "hvs"
        return None
