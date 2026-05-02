from __future__ import annotations
from dataclasses import dataclass

from .incident_type import IncidentType


@dataclass
class Incident:
    incident_id: int
    incident_type: IncidentType
    severity: float
    location_id: int  # ID of node | edge
    location_type: str  # node | edge
    start_time: int
    duration: int = 0  # incident duration
    spread_count: int = 0
    
    def __post_init__(self):
        base_duration = {
            IncidentType.GVS_RISER_FAILURE: 18,
            IncidentType.GVS_PIPE_FAILURE: 12,
            IncidentType.HVS_RISER_FAILURE: 18,
            IncidentType.HVS_PIPE_FAILURE: 12,
        }.get(self.incident_type, 15)
        
        self.duration = int(base_duration * (1 + self.severity))
    
    @property
    def is_active(self) -> bool:
        return self.duration > 0
    
    def update(self) -> None:
        if self.is_active:
            decay = self.incident_type.decay_rate
            self.severity = max(0, self.severity - decay)
            self.duration -= 1
