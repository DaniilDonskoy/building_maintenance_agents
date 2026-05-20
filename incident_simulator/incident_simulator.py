from __future__ import annotations

from typing import List, Optional, Dict, Any
from collections import defaultdict

import torch
from loguru import logger

from house_graph.house import House
from house_graph.nodes import BaseNode
from .incident import Incident
from .incident_type import IncidentType

from .incident import Incident
from .incident_spawner import IncidentSpawner
from .incident_propagation import IncidentPropagation


class IncidentSimulator:

    def __init__(
        self,
        house: House,
        base_incident_probability: float = 1.0,
        random_seed: Optional[int] = None,
        enable_spread: bool = True,
        passive_incident_decay: bool = True,  # NEW
        auto_resolve_incidents: bool = True,   # NEW
        max_incident_age: int = 72             # NEW: максимальный возраст до просрочки
    ):
        self.house = house
        self.enable_spread = enable_spread
        self.passive_incident_decay = passive_incident_decay
        self.auto_resolve_incidents = auto_resolve_incidents
        self.max_incident_age = max_incident_age
        self.time_step = 0

        self.node_by_id = {id(node): node for node in house.nodes}
        self.edge_by_id = {id(edge): edge for edge in house.edges}

        self.node_edges = {id(node): [] for node in house.nodes}
        self.node_nodes = {id(node): [] for node in house.nodes}
        self._build_adjacency_cache()

        self.active_incidents: List[Incident] = []
        self.incident_history: List[Incident] = []
        self.next_incident_id = 0

        self.spawner = IncidentSpawner(
            base_probability=base_incident_probability,
            random_seed=random_seed
        )

        if enable_spread:
            self.propagator = IncidentPropagation(self)

        self.stats = {
            "total_incidents": 0,
            "incidents_by_type": defaultdict(int),
            "max_active_incidents": 0,
            "total_damage": 0.0,
            "total_overdue": 0
        }

        logger.info(
            f"IncidentSimulator initialized with {len(house.nodes)} nodes, {len(house.edges)} edges")
        logger.info(f"Base incident probability: {base_incident_probability}")
        logger.info(f"Passive incident decay: {passive_incident_decay}")
        logger.info(f"Auto resolve incidents: {auto_resolve_incidents}")
        logger.info(f"Max incident age: {max_incident_age}")

    def _build_adjacency_cache(self):
        for edge in self.house.edges:
            node_a_id = id(edge.node_a)
            node_b_id = id(edge.node_b)

            self.node_edges[node_a_id].append((id(edge), node_b_id))
            self.node_edges[node_b_id].append((id(edge), node_a_id))
            self.node_nodes[node_a_id].append(node_b_id)
            self.node_nodes[node_b_id].append(node_a_id)

    def step(self) -> Dict[str, Any]:
        self.time_step += 1

        results = {
            "time_step": self.time_step,
            "new_incidents": [],
            "resolved_incidents": [],
            "spread_incidents": [],
            "active_count": len(self.active_incidents),
            "overdue_count": sum(1 for inc in self.active_incidents if inc.is_overdue)
        }

        self._update_existing_incidents(results)
        self._spawn_new_incidents(results)
        if self.enable_spread:
            self._spread_incidents(results)

        self._update_stats()

        return results

    def _update_existing_incidents(self, results: Dict):
        incidents_to_remove = []

        for incident in self.active_incidents:
            incident.update()

            # Применяем пассивное ухудшение инцидента, если включено
            if self.passive_incident_decay and incident.is_active:
                # Проверяем просрочку
                if incident.is_overdue and not hasattr(incident, '_overdue_logged'):
                    incident._overdue_logged = True
                    logger.warning(
                        f"Incident {incident.incident_id} is now OVERDUE! age={incident._get_age()}")

            element = self._get_element(
                incident.location_id, incident.location_type)
            if element and incident.is_active:
                status = "OVERDUE" if incident.is_overdue else "active"
                element.incident_state.update_incident(
                    f"{incident.incident_type.value}: severity {incident.severity:.2f} [{status}]"
                )

            # Автоматическое разрешение инцидента, если включено
            if self.auto_resolve_incidents and (incident.severity <= 0.01 or not incident.is_active):
                incident.duration = 0
                results["resolved_incidents"].append({
                    "id": incident.incident_id,
                    "type": incident.incident_type.value,
                    "location": incident.location_id,
                    "duration": incident.duration,
                    "was_overdue": incident.is_overdue,
                    "age": incident._get_age()
                })
                incidents_to_remove.append(incident)

                element = self._get_element(
                    incident.location_id, incident.location_type)
                if element:
                    element.incident_state.fix_incident()

        for incident in incidents_to_remove:
            self.active_incidents.remove(incident)
            self.incident_history.append(incident)

    def _spawn_new_incidents(self, results: Dict):
        for node in self.house.nodes:
            should_spawn, inc_type, severity = self.spawner.should_spawn(
                node, "node", self.time_step, self.active_incidents
            )

            if should_spawn:
                incident = self._create_incident(
                    inc_type, severity, id(node), "node"
                )
                if incident:
                    results["new_incidents"].append({
                        "id": incident.incident_id,
                        "type": inc_type.value,
                        "location": id(node),
                        "severity": severity
                    })

        for edge in self.house.edges:
            should_spawn, inc_type, severity = self.spawner.should_spawn(
                edge, "edge", self.time_step, self.active_incidents
            )

            if should_spawn:
                incident = self._create_incident(
                    inc_type, severity, id(edge), "edge"
                )
                if incident:
                    results["new_incidents"].append({
                        "id": incident.incident_id,
                        "type": inc_type.value,
                        "location": id(edge),
                        "severity": severity
                    })

    def _spread_incidents(self, results: Dict):
        for incident in self.active_incidents[:]:
            if incident.severity > 0.3 and not incident.is_overdue:
                new_locations = self.propagator.propagate(incident)
                if new_locations:
                    results["spread_incidents"].append({
                        "source": incident.incident_id,
                        "new_locations": new_locations
                    })

    def _create_incident(
        self,
        inc_type: IncidentType,
        severity: float,
        location_id: int,
        location_type: str
    ) -> Optional[Incident]:

        element = self._get_element(location_id, location_type)
        if not element:
            return None

        for inc in self.active_incidents:
            if inc.location_id == location_id and inc.location_type == location_type:
                return None

        incident = Incident(
            incident_id=self.next_incident_id,
            incident_type=inc_type,
            severity=severity,
            location_id=location_id,
            location_type=location_type,
            start_time=self.time_step,
            max_duration=self.max_incident_age
        )

        self.next_incident_id += 1
        self.active_incidents.append(incident)

        element.incident_state.set_incident(
            f"{inc_type.value} started with severity {severity:.2f}"
        )

        self.stats["total_incidents"] += 1
        self.stats["incidents_by_type"][inc_type.value] += 1
        self.stats["total_damage"] += severity

        logger.debug(
            f"New incident: {inc_type.value} at {location_type} {location_id}, severity={severity:.2f}")

        return incident

    def _get_element(self, element_id: int, element_type: str):
        if element_type == "node":
            return self.node_by_id.get(element_id)
        elif element_type == "edge":
            return self.edge_by_id.get(element_id)
        return None

    def _update_stats(self):
        active_count = len(self.active_incidents)
        overdue_count = sum(
            1 for inc in self.active_incidents if inc.is_overdue)

        if active_count > self.stats["max_active_incidents"]:
            self.stats["max_active_incidents"] = active_count

        if overdue_count > self.stats.get("max_overdue", 0):
            self.stats["max_overdue"] = overdue_count

        self.stats["total_overdue"] = max(
            self.stats["total_overdue"], overdue_count)

    def create_incident(
        self,
        incident_type: IncidentType,
        element,
        severity: float = 0.5
    ) -> Optional[Incident]:
        element_id = id(element)
        element_type = "node" if isinstance(element, BaseNode) else "edge"

        return self._create_incident(
            incident_type, severity, element_id, element_type
        )

    def resolve_incident(self, incident_id: int) -> bool:
        for incident in self.active_incidents:
            if incident.incident_id == incident_id:
                incident.duration = 0
                incident.severity = 0
                return True
        return False

    def get_incidents_on_element(self, element) -> List[Incident]:
        element_id = id(element)
        return [
            inc for inc in self.active_incidents
            if inc.location_id == element_id
        ]

    def get_incident_tensors(self) -> Dict[str, torch.Tensor]:
        node_incident = torch.zeros(len(self.house.nodes), dtype=torch.float32)
        node_incident_severity = torch.zeros(
            len(self.house.nodes), dtype=torch.float32)
        node_incident_type = torch.zeros(
            len(self.house.nodes), len(IncidentType), dtype=torch.float32)

        for idx, node in enumerate(self.house.nodes):
            node_id = id(node)
            incidents = [
                inc for inc in self.active_incidents if inc.location_id == node_id]

            if incidents:
                node_incident[idx] = 1.0
                worst_incident = max(incidents, key=lambda x: x.severity)
                node_incident_severity[idx] = worst_incident.severity

                type_idx = list(IncidentType).index(
                    worst_incident.incident_type)
                node_incident_type[idx, type_idx] = 1.0

        edge_incident = torch.zeros(len(self.house.edges), dtype=torch.float32)
        edge_incident_severity = torch.zeros(
            len(self.house.edges), dtype=torch.float32)
        edge_incident_type = torch.zeros(
            len(self.house.edges), len(IncidentType), dtype=torch.float32)

        for idx, edge in enumerate(self.house.edges):
            edge_id = id(edge)
            incidents = [
                inc for inc in self.active_incidents if inc.location_id == edge_id]

            if incidents:
                edge_incident[idx] = 1.0
                worst_incident = max(incidents, key=lambda x: x.severity)
                edge_incident_severity[idx] = worst_incident.severity

                type_idx = list(IncidentType).index(
                    worst_incident.incident_type)
                edge_incident_type[idx, type_idx] = 1.0

        return {
            "node_incident": node_incident,
            "node_incident_severity": node_incident_severity,
            "node_incident_type": node_incident_type,
            "edge_incident": edge_incident,
            "edge_incident_severity": edge_incident_severity,
            "edge_incident_type": edge_incident_type,
        }

    def get_affected_elements(self) -> Dict[str, List]:
        affected_nodes = []
        affected_edges = []

        for node in self.house.nodes:
            if node.incident_state.has_incident:
                affected_nodes.append(node)

        for edge in self.house.edges:
            if edge.incident_state.has_incident:
                affected_edges.append(edge)

        return {
            "nodes": affected_nodes,
            "edges": affected_edges
        }

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "current_time": self.time_step,
            "active_incidents": len(self.active_incidents),
            "overdue_incidents": sum(1 for inc in self.active_incidents if inc.is_overdue),
            "average_severity": sum(i.severity for i in self.active_incidents) / max(1, len(self.active_incidents))
        }

    def reset(self) -> None:
        for incident in self.active_incidents:
            element = self._get_element(
                incident.location_id, incident.location_type)
            if element:
                element.incident_state.fix_incident()

        self.active_incidents.clear()
        self.incident_history.clear()
        self.time_step = 0

        self.stats = {
            "total_incidents": 0,
            "incidents_by_type": defaultdict(int),
            "max_active_incidents": 0,
            "total_damage": 0.0,
            "total_overdue": 0,
            "max_overdue": 0
        }

        logger.info("IncidentSimulator reset")
