from __future__ import annotations

import numpy as np
from typing import Optional

from incident_simulator import IncidentSimulator
from .incident_observation import IncidentObservation
from .element_state import AgentStateMachine


class BuildingIncidentCore:

    def __init__(self, simulator: IncidentSimulator, max_active_incidents: int):
        self.simulator = simulator
        self.max_active_incidents = max_active_incidents
        self.observer = IncidentObservation(simulator, state_machine=None)
        self.node_ids = [id(node) for node in simulator.house.nodes]
        self.edge_ids = [id(edge) for edge in simulator.house.edges]
        self.node_by_id = {id(node): node for node in simulator.house.nodes}
        self.edge_by_id = {id(edge): edge for edge in simulator.house.edges}
        self.max_targets = max(len(self.node_ids), len(self.edge_ids))

    def get_observation(self, state_machine: Optional[AgentStateMachine] = None, building_idx: int = 0) -> np.ndarray:
        return self.observer.get_observation(state_machine, building_idx)
