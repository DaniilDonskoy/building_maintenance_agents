from __future__ import annotations
from enum import Enum


class IncidentType(Enum):
    GVS_RISER_FAILURE = "gvs_riser_failure"
    GVS_PIPE_FAILURE = "gvs_pipe_failure"
    HVS_RISER_FAILURE = "hvs_riser_failure"
    HVS_PIPE_FAILURE = "hvs_pipe_failure"
    
    @property
    def base_probability(self) -> float:
        probabilities = {
            "gvs_riser_failure": 76 / 972000,
            "gvs_pipe_failure": 40 / 3240000,
            "hvs_riser_failure": 11 / 972000,
            "hvs_pipe_failure": 8 / 3240000,
        }
        return probabilities[self.value]
    
    @property
    def decay_rate(self) -> float:
        rates = {
            "gvs_riser_failure": 0.03,
            "gvs_pipe_failure": 0.04,
            "hvs_riser_failure": 0.03,
            "hvs_pipe_failure": 0.04,
        }
        return rates[self.value]
    
    @property
    def spread_radius(self) -> int:
        radii = {
            "gvs_riser_failure": 1,
            "gvs_pipe_failure": 1,
            "hvs_riser_failure": 1,
            "hvs_pipe_failure": 1,
        }
        return radii[self.value]
