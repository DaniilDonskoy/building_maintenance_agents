from __future__ import annotations

import random
from typing import List, Tuple

from .incident import Incident


class IncidentPropagation:
    
    def __init__(self, simulator):
        self.simulator = simulator
    
    def propagate(self, incident: Incident) -> List[int]:
        if incident.incident_type.spread_radius == 0:
            return []
        
        if incident.spread_count >= incident.incident_type.spread_radius:
            return []
        
        if incident.location_type == "node":
            neighbors = self._get_node_neighbors(incident.location_id)
        else:
            neighbors = self._get_edge_neighbors(incident.location_id)
        
        spread_probability = incident.severity * 0.3
        
        new_locations = []
        
        for neighbor_id, neighbor_type in neighbors:
            has_incident = False
            for inc in self.simulator.active_incidents:
                if inc.location_id == neighbor_id and inc.location_type == neighbor_type:
                    has_incident = True
                    break
            
            if not has_incident and random.random() < spread_probability:
                new_incident = Incident(
                    incident_id=self.simulator.next_incident_id,
                    incident_type=incident.incident_type,
                    severity=incident.severity * 0.6,
                    location_id=neighbor_id,
                    location_type=neighbor_type,
                    start_time=self.simulator.time_step
                )
                
                self.simulator.next_incident_id += 1
                self.simulator.active_incidents.append(new_incident)
                new_locations.append(neighbor_id)
                
                if neighbor_type == "node":
                    node = self.simulator.node_by_id[neighbor_id]
                    node.incident_state.set_incident(f"{incident.incident_type.value} spread from {incident.location_id}")
                else:
                    edge = self.simulator.edge_by_id[neighbor_id]
                    edge.incident_state.set_incident(f"{incident.incident_type.value} spread from {incident.location_id}")
        
        incident.spread_count += 1
        return new_locations
    
    def _get_node_neighbors(self, node_id: int) -> List[Tuple[int, str]]:
        neighbors = []
        
        for neighbor_id in self.simulator.node_nodes.get(node_id, []):
            neighbors.append((neighbor_id, "node"))
        
        for edge_id, _ in self.simulator.node_edges.get(node_id, []):
            neighbors.append((edge_id, "edge"))
        
        return neighbors
    
    def _get_edge_neighbors(self, edge_id: int) -> List[Tuple[int, str]]:
        neighbors = []
        
        edge = self.simulator.edge_by_id.get(edge_id)
        if edge:
            node_a_id = id(edge.node_a)
            node_b_id = id(edge.node_b)
            neighbors.append((node_a_id, "node"))
            neighbors.append((node_b_id, "node"))
        
        return neighbors