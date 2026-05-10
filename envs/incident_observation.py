from __future__ import annotations

import numpy as np
from typing import Dict, List
from collections import defaultdict

from incident_simulator import (
    IncidentSimulator, IncidentType, Incident
)
from house_graph.nodes import TechNode, ElecNode, FlatNode, RiserNode, ElevNode, MopNode
from house_graph.edges import PathEdge


class IncidentObservation:
    
    def __init__(self, simulator: IncidentSimulator):
        self.simulator = simulator
        self._normalization_stats = self._compute_normalization_stats()
    
    def _compute_normalization_stats(self) -> Dict[str, Dict[str, float]]:
        node_degrees = []
        node_criticality = []
        
        for node in self.simulator.house.nodes:
            node_degrees.append(len(self.simulator.node_nodes.get(id(node), [])))
            node_criticality.append(self._compute_node_criticality(node))
        
        return {
            "degree": {"mean": np.mean(node_degrees), "std": max(np.std(node_degrees), 1)},
            "criticality": {"mean": np.mean(node_criticality), "std": max(np.std(node_criticality), 1)}
        }
    
    def _compute_node_criticality(self, node) -> float:
        criticality = 0.0
        
        node_type = type(node).__name__
        type_weights = {
            'TechNode': 0.9,
            'ElecNode': 0.8,
            'RiserNode': 0.7,
            'ElevNode': 0.6,
            'MopNode': 0.4,
            'FlatNode': 0.3
        }
        criticality += type_weights.get(node_type, 0.5)
        
        degree = len(self.simulator.node_nodes.get(id(node), []))
        max_degree = max(len(v) for v in self.simulator.node_nodes.values()) if self.simulator.node_nodes else 1
        criticality += degree / max_degree * 0.3
        
        return min(criticality, 1.0)
    
    def get_observation(self) -> np.ndarray:
        node_features = self._get_node_features()
        edge_features = self._get_edge_features()
        global_features = self._get_global_features()
        incident_features = self._get_incident_features()
        
        observation = np.concatenate([node_features, edge_features, global_features, incident_features])
        
        return observation.astype(np.float32)
    
    def _get_node_features(self) -> np.ndarray:
        features = []
        
        for node in self.simulator.house.nodes:
            node_id = id(node)
            
            node_type_id = self._get_node_type_id(node)
            degree = len(self.simulator.node_nodes.get(node_id, []))
            normalized_degree = degree / self._normalization_stats["degree"]["mean"] if self._normalization_stats["degree"]["mean"] > 0 else 0
            criticality = self._compute_node_criticality(node)
            normalized_criticality = (criticality - self._normalization_stats["criticality"]["mean"]) / self._normalization_stats["criticality"]["std"]
            
            incidents = [inc for inc in self.simulator.active_incidents if inc.location_id == node_id]
            has_incident = 1.0 if incidents else 0.0
            max_severity = max([inc.severity for inc in incidents]) if incidents else 0.0
            incident_types = self._get_incident_type_vector(incidents)
            
            x = node.features.get('x', 0) / 100.0
            y = node.features.get('y', 0) / 100.0
            z = node.features.get('z', 0) / 100.0
            
            node_vector = [
                node_type_id,
                normalized_degree,
                normalized_criticality,
                has_incident,
                max_severity,
                x, y, z
            ] + incident_types
            
            features.extend(node_vector)
        
        return np.array(features)
    
    def _get_node_type_id(self, node) -> float:
        type_mapping = {
            TechNode: 0.0,
            ElecNode: 0.2,
            MopNode: 0.4,
            FlatNode: 0.6,
            RiserNode: 0.8,
            ElevNode: 1.0
        }
        return type_mapping.get(type(node), 0.5)
    
    def _get_incident_type_vector(self, incidents: List[Incident]) -> List[float]:
        vector = [0.0] * len(IncidentType)
        for inc in incidents:
            idx = list(IncidentType).index(inc.incident_type)
            vector[idx] = max(vector[idx], inc.severity)
        return vector
    
    def _get_edge_features(self) -> np.ndarray:
        features = []
        
        for edge in self.simulator.house.edges:
            edge_id = id(edge)
            
            edge_type_id = 0.0 if isinstance(edge, PathEdge) else 1.0
            
            length = self._compute_edge_length(edge)
            
            incidents = [inc for inc in self.simulator.active_incidents if inc.location_id == edge_id]
            has_incident = 1.0 if incidents else 0.0
            max_severity = max([inc.severity for inc in incidents]) if incidents else 0.0
            incident_types = self._get_incident_type_vector(incidents)
            
            oriented = 1.0 if edge.oriented else 0.0
            
            edge_vector = [
                edge_type_id,
                length,
                has_incident,
                max_severity,
                oriented
            ] + incident_types
            
            features.extend(edge_vector)
        
        return np.array(features)
    
    def _compute_edge_length(self, edge) -> float:
        node_a = edge.node_a
        node_b = edge.node_b
        
        dx = node_a.features.get('x', 0) - node_b.features.get('x', 0)
        dy = node_a.features.get('y', 0) - node_b.features.get('y', 0)
        dz = node_a.features.get('z', 0) - node_b.features.get('z', 0)
        
        distance = np.sqrt(dx**2 + dy**2 + dz**2)
        return min(distance / 50.0, 1.0)
    
    def _get_global_features(self) -> np.ndarray:
        active_incidents = len(self.simulator.active_incidents)
        total_severity = sum(inc.severity for inc in self.simulator.active_incidents)
        avg_severity = total_severity / max(1, active_incidents)
        
        type_counts = defaultdict(int)
        for inc in self.simulator.active_incidents:
            type_counts[inc.incident_type] += 1
        
        type_vector = [type_counts.get(t, 0) / max(1, active_incidents) for t in IncidentType]
        
        time_normalized = self.simulator.time_step / 100.0
        
        affected_elements = self.simulator.house.incident_count
        
        total_elements = len(self.simulator.house.nodes) + len(self.simulator.house.edges)
        affected_ratio = affected_elements / max(1, total_elements)
        
        global_vector = [
            active_incidents / 10.0,
            avg_severity,
            affected_ratio,
            time_normalized
        ] + type_vector
        
        return np.array(global_vector)
    
    def _get_incident_features(self) -> np.ndarray:
        features = []
        
        top_incidents = sorted(
            self.simulator.active_incidents,
            key=lambda x: x.severity,
            reverse=True
        )[:5]
        
        for inc in top_incidents:
            inc_features = [
                list(IncidentType).index(inc.incident_type) / len(IncidentType),
                inc.severity,
                inc.duration / 100.0,
                inc.spread_count / max(1, inc.incident_type.spread_radius),
                inc.start_time / 100.0
            ]
            features.extend(inc_features)
        
        while len(features) < 25:
            features.append(0.0)
        
        return np.array(features[:25])
