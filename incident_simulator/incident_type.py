from __future__ import annotations
from enum import Enum


class IncidentType(Enum):
    FIRE = "fire"
    FLOOD = "flood"
    POWER_OUTAGE = "power_outage"
    ELEVATOR_FAILURE = "elevator_failure"
    BLOCKAGE = "blockage"
    GAS_LEAK = "gas_leak"
    SMOKE = "smoke"
    STRUCTURAL_DAMAGE = "structural_damage"
    
    @property
    def base_probability(self) -> float:
        probabilities = {
            "fire": 0.001,
            "flood": 0.002,
            "power_outage": 0.003,
            "elevator_failure": 0.0005,
            "blockage": 0.001,
            "gas_leak": 0.0005,
            "smoke": 0.001,
            "structural_damage": 0.0002
        }
        return probabilities[self.value]
    
    @property
    def decay_rate(self) -> float:
        rates = {
            "fire": 0.05,
            "flood": 0.03,
            "power_outage": 0.1,
            "elevator_failure": 0.02,
            "blockage": 0.04,
            "gas_leak": 0.06,
            "smoke": 0.08,
            "structural_damage": 0.01
        }
        return rates[self.value]
    
    @property
    def spread_radius(self) -> int:
        radii = {
            "fire": 2,
            "flood": 1,
            "power_outage": 3,
            "elevator_failure": 0,
            "blockage": 1,
            "gas_leak": 2,
            "smoke": 2,
            "structural_damage": 1
        }
        return radii[self.value]
