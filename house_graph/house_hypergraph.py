from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import torch
from dto import HouseTensorDTO


NODE_TYPES = ("APT", "MOP", "LIFT", "RISER", "PANEL", "ITP", "TECH", "ROOF")
EDGE_TYPES = ("ADJ", "HEAT", "COLD", "HOT", "ELEC", "VENT", "DRAIN")


@dataclass(slots=True)
class Node:
    id: str
    type: str
    features: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in NODE_TYPES:
            raise ValueError(f"Unknown node type: {self.type}")
        if any(coord not in self.features for coord in ("x", "y", "z")):
            raise ValueError("Node features must include 'x', 'y', and 'z' coordinates")
        self.features = {k: float(v) for k, v in self.features.items()}


@dataclass(slots=True)
class Edge:
    id: str
    type: str
    node_ids: List[str]
    features: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in EDGE_TYPES:
            raise ValueError(f"Unknown edge type: {self.type}")
        if len(self.node_ids) < 2:
            raise ValueError("Edge must connect at least two nodes")
        self.features = {k: float(v) for k, v in self.features.items()}


@dataclass
class House:
    id: str
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        if any(n.id == node.id for n in self.nodes):
            raise ValueError(f"Duplicate node id: {node.id}")
        self.nodes.append(node)

    def add_edge(self, edge: Edge) -> None:
        node_ids = {n.id for n in self.nodes}
        missing = [nid for nid in edge.node_ids if nid not in node_ids]
        if missing:
            raise ValueError(f"Edge {edge.id} references missing nodes: {missing}")
        if any(e.id == edge.id for e in self.edges):
            raise ValueError(f"Duplicate edge id: {edge.id}")
        self.edges.append(edge)

    def to_tensors(self) -> dict:
        node_index = {node.id: i for i, node in enumerate(self.nodes)}
        edge_type_index = {edge_type: i for i, edge_type in enumerate(EDGE_TYPES)}
        node_features = sorted({k for n in self.nodes for k in n.features})
        edge_features = sorted({k for e in self.edges for k in e.features})

        node_attr = torch.zeros((len(self.nodes), len(node_features)), dtype=torch.float32)
        for i, node in enumerate(self.nodes):
            for j, name in enumerate(node_features):
                node_attr[i, j] = node.features.get(name, 0.0)

        edge_attr = torch.zeros((len(self.edges), len(edge_features)), dtype=torch.float32)
        for i, edge in enumerate(self.edges):
            for j, name in enumerate(edge_features):
                edge_attr[i, j] = edge.features.get(name, 0.0)

        node_type = torch.zeros((len(self.nodes), len(NODE_TYPES)), dtype=torch.float32)
        for i, node in enumerate(self.nodes):
            node_type[i, NODE_TYPES.index(node.type)] = 1.0

        incidence = torch.zeros((len(EDGE_TYPES), len(self.edges), len(self.nodes)), dtype=torch.float32)
        for e_idx, edge in enumerate(self.edges):
            t_idx = edge_type_index[edge.type]
            for node_id in edge.node_ids:
                incidence[t_idx, e_idx, node_index[node_id]] = 1.0

        return HouseTensorDTO(
            node_attr=node_attr,
            node_type=node_type,
            edge_attr=edge_attr,
            incidence=incidence,
            node_ids=[n.id for n in self.nodes],
            edge_ids=[e.id for e in self.edges],
            node_feature_names=node_features,
            edge_feature_names=edge_features,
        )


class HouseFactory:
    floors = 1
    sections = 1
    apartments_per_section = 1
    lifts_per_section = 1
    risers_per_section = 1
    floor_height = 3.0
    section_spacing = 30.0
    apartment_spacing = 6.0

    @classmethod
    def _features(cls, x: float, y: float, z: float, **extra: float) -> Dict[str, float]:
        return {"x": x, "y": y, "z": z, **extra}

    @classmethod
    def build(cls, house_id: str) -> House:
        house = House(house_id)
        center_x = (cls.sections - 1) * cls.section_spacing / 2
        roof_z = cls.floors * cls.floor_height
        house.add_node(Node("itp_1", "ITP", cls._features(center_x - 4, -6, 0, floor=0, shared=1)))
        house.add_node(Node("tech_1", "TECH", cls._features(center_x + 4, -6, 0, floor=0, shared=1)))
        house.add_node(Node("roof_1", "ROOF", cls._features(center_x, 0, roof_z, floor=cls.floors + 1, shared=1)))

        section_panels, section_risers, section_lifts, section_mops = {}, {}, {}, {}
        for section in range(1, cls.sections + 1):
            section_panels[section] = []
            section_risers[section] = []
            section_lifts[section] = []
            section_mops[section] = []
            section_x = (section - 1) * cls.section_spacing
            for floor in range(1, cls.floors + 1):
                z = (floor - 1) * cls.floor_height
                mop_id = f"mop_{section}_{floor}"
                panel_id = f"panel_{section}_{floor}"
                house.add_node(Node(mop_id, "MOP", cls._features(section_x, 0, z, floor=floor, section=section)))
                house.add_node(Node(panel_id, "PANEL", cls._features(section_x - 3, -2, z, floor=floor, section=section)))
                section_mops[section].append(mop_id)
                section_panels[section].append(panel_id)

                apt_ids, riser_ids, lift_ids = [], [], []
                for i in range(1, cls.apartments_per_section + 1):
                    apt_id = f"apt_{section}_{floor}_{i}"
                    apt_ids.append(apt_id)
                    apt_x = section_x + (i - (cls.apartments_per_section + 1) / 2) * cls.apartment_spacing
                    house.add_node(Node(apt_id, "APT", cls._features(apt_x, 6, z, floor=floor, section=section, rooms=1 + (i % 3))))
                for i in range(1, cls.lifts_per_section + 1):
                    lift_id = f"lift_{section}_{floor}_{i}"
                    lift_ids.append(lift_id)
                    lift_x = section_x - 2 + 1.5 * (i - 1)
                    house.add_node(Node(lift_id, "LIFT", cls._features(lift_x, 1.5, z, floor=floor, section=section, shaft=i)))
                    section_lifts[section].append(lift_id)
                for i in range(1, cls.risers_per_section + 1):
                    riser_id = f"riser_{section}_{floor}_{i}"
                    riser_ids.append(riser_id)
                    riser_x = section_x + 2 + 1.5 * (i - 1)
                    house.add_node(Node(riser_id, "RISER", cls._features(riser_x, -1.5, z, floor=floor, section=section, shaft=i)))
                    section_risers[section].append(riser_id)

                house.add_edge(Edge(f"adj_{section}_{floor}", "ADJ", [mop_id, *apt_ids, *lift_ids, *riser_ids], {"floor": floor, "section": section}))
                house.add_edge(Edge(f"elec_floor_{section}_{floor}", "ELEC", [panel_id, *apt_ids, *lift_ids], {"floor": floor, "section": section}))
                house.add_edge(Edge(f"vent_floor_{section}_{floor}", "VENT", ["tech_1", mop_id, *apt_ids, "roof_1"], {"floor": floor, "section": section}))

                for i, riser_id in enumerate(riser_ids, start=1):
                    attached_apts = apt_ids[i - 1 :: len(riser_ids)]
                    if attached_apts:
                        base = {"floor": floor, "section": section, "shaft": i}
                        house.add_edge(Edge(f"heat_{section}_{floor}_{i}", "HEAT", ["itp_1", riser_id, *attached_apts], base))
                        house.add_edge(Edge(f"cold_{section}_{floor}_{i}", "COLD", [riser_id, *attached_apts], base))
                        house.add_edge(Edge(f"hot_{section}_{floor}_{i}", "HOT", ["itp_1", riser_id, *attached_apts], base))
                        house.add_edge(Edge(f"drain_{section}_{floor}_{i}", "DRAIN", [riser_id, *attached_apts, "tech_1"], base))

        for section in range(1, cls.sections + 1):
            house.add_edge(Edge(f"elec_shaft_{section}", "ELEC", ["tech_1", *section_panels[section]], {"section": section, "vertical": 1}))
            house.add_edge(Edge(f"heat_shaft_{section}", "HEAT", ["itp_1", *section_risers[section]], {"section": section, "vertical": 1}))
            house.add_edge(Edge(f"cold_shaft_{section}", "COLD", section_risers[section], {"section": section, "vertical": 1}))
            house.add_edge(Edge(f"hot_shaft_{section}", "HOT", ["itp_1", *section_risers[section]], {"section": section, "vertical": 1}))
            house.add_edge(Edge(f"drain_shaft_{section}", "DRAIN", [*section_risers[section], "tech_1"], {"section": section, "vertical": 1}))
            house.add_edge(Edge(f"vent_shaft_{section}", "VENT", ["tech_1", *section_mops[section], "roof_1"], {"section": section, "vertical": 1}))
            house.add_edge(Edge(f"lift_shaft_{section}", "ADJ", section_lifts[section], {"section": section, "vertical": 1}))

        return house


class House15Factory(HouseFactory):
    floors = 15
    sections = 2
    apartments_per_section = 3
    lifts_per_section = 1
    risers_per_section = 1


class House16Factory(HouseFactory):
    floors = 16
    sections = 2
    apartments_per_section = 6
    lifts_per_section = 2
    risers_per_section = 2


class House27Factory(HouseFactory):
    floors = 27
    sections = 4
    apartments_per_section = 5
    lifts_per_section = 2
    risers_per_section = 2
