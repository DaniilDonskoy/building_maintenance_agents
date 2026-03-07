from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import torch


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
        self.features = {k: float(v) for k, v in self.features.items()}


@dataclass(slots=True)
class Edge:
    id: str
    type: str
    node_ids: List[str]

    def __post_init__(self) -> None:
        if self.type not in EDGE_TYPES:
            raise ValueError(f"Unknown edge type: {self.type}")
        if len(self.node_ids) < 2:
            raise ValueError("Edge must connect at least two nodes")


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
        edge_index = {edge.id: i for i, edge in enumerate(self.edges)}
        edge_type_index = {etype: i for i, etype in enumerate(EDGE_TYPES)}

        feature_names = sorted({name for n in self.nodes for name in n.features})
        x = torch.zeros((len(self.nodes), len(feature_names)), dtype=torch.float32)
        for i, node in enumerate(self.nodes):
            for j, name in enumerate(feature_names):
                if name in node.features:
                    x[i, j] = node.features[name]

        node_type = torch.zeros((len(self.nodes), len(NODE_TYPES)), dtype=torch.float32)
        for i, node in enumerate(self.nodes):
            node_type[i, NODE_TYPES.index(node.type)] = 1.0

        incidence = torch.zeros(
            (len(EDGE_TYPES), len(self.edges), len(self.nodes)), dtype=torch.float32
        )
        for e_idx, edge in enumerate(self.edges):
            t_idx = edge_type_index[edge.type]
            for node_id in edge.node_ids:
                n_idx = node_index[node_id]
                incidence[t_idx, e_idx, n_idx] = 1.0

        return {
            # Набор признаков для каждого узла (размер: num_nodes x num_features)
            "x": x,
            # One-hot кодирование типа узла (размер: num_nodes x num_node_types)
            "node_type": node_type,
            # Инцидентная матрица (размер: num_edge_types x num_edges x num_nodes)
            "incidence": incidence,
            # Списки идентификаторов узлов и рёбер для удобства (index = идентификатор)
            "node_ids": list(node_index.keys()),
            "edge_ids": list(edge_index.keys()),
            # Список названий признаков для удобства
            "feature_names": feature_names,
        }


if __name__ == "__main__":
    house = House(id="house_1")

    house.add_node(Node("apt_1", "APT", {"area": 54, "floor": 1}))
    house.add_node(Node("apt_2", "APT", {"area": 48, "floor": 2}))
    house.add_node(Node("mop_1", "MOP", {"floor": 1}))
    house.add_node(Node("lift_1", "LIFT", {"floor": 1}))
    house.add_node(Node("riser_1", "RISER", {"floor": 1}))
    house.add_node(Node("panel_1", "PANEL", {"floor": 1}))
    house.add_node(Node("itp_1", "ITP", {"floor": 0}))
    house.add_node(Node("tech_1", "TECH", {"floor": 0}))
    house.add_node(Node("roof_1", "ROOF", {"floor": 2}))

    house.add_edge(Edge("adj_1", "ADJ", ["apt_1", "mop_1", "lift_1"]))
    house.add_edge(Edge("adj_2", "ADJ", ["apt_2", "riser_1", "panel_1"]))
    house.add_edge(Edge("heat_1", "HEAT", ["itp_1", "riser_1", "apt_1"]))
    house.add_edge(Edge("cold_1", "COLD", ["riser_1", "apt_1"]))
    house.add_edge(Edge("hot_1", "HOT", ["itp_1", "riser_1", "apt_1"]))
    house.add_edge(Edge("elec_1", "ELEC", ["panel_1", "apt_1", "lift_1"]))
    house.add_edge(Edge("vent_1", "VENT", ["tech_1", "apt_1", "roof_1"]))
    house.add_edge(Edge("drain_1", "DRAIN", ["apt_1", "riser_1", "tech_1"]))

    tensors = house.to_tensors()
    for name, value in tensors.items():
        print(f"{name}:\n{value}\n")
