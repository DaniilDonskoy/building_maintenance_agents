from __future__ import annotations

import torch
from dataclasses import dataclass, field
from typing import List

from .dto import HouseGraphDTO, HouseTensorDTO
from .nodes import BaseNode
from .edges import BaseEdge


@dataclass
class House:
    nodes: List[BaseNode] = field(default_factory=list)
    edges: List[BaseEdge] = field(default_factory=list)

    def add_node(self, node: BaseNode) -> None:
        self.nodes.append(node)

    def add_edge(self, edge: BaseEdge) -> None:
        self.edges.append(edge)

    def to_tensors(self) -> HouseTensorDTO:
        """Convert the house graph into a tensor-based DTO.

        This method automatically derives node and edge types from their runtime
        classes so the graph can grow with new node/edge kinds without changes.
        """

        node_feature_names = sorted({
            key
            for node in self.nodes
            for key in node.features
        })
        node_types = sorted({type(node).__name__ for node in self.nodes})

        node_attr = torch.zeros((len(self.nodes), len(node_feature_names)), dtype=torch.float32)
        node_type = torch.zeros((len(self.nodes), len(node_types)), dtype=torch.float32)
        for node_idx, node in enumerate(self.nodes):
            node_type[node_idx, node_types.index(type(node).__name__)] = 1.0
            for feat_key, feat_value in node.features.items():
                node_attr[node_idx, node_feature_names.index(feat_key)] = float(feat_value)

        edge_feature_names = sorted({
            key
            for edge in self.edges
            for key in edge.features.keys()
        })
        edge_types = sorted({type(edge).__name__ for edge in self.edges})

        edge_attr = torch.zeros((len(self.edges), len(edge_feature_names)), dtype=torch.float32)
        edge_type = torch.zeros((len(self.edges), len(edge_types)), dtype=torch.float32)
        for edge_idx, edge in enumerate(self.edges):
            edge_type[edge_idx, edge_types.index(type(edge).__name__)] = 1.0
            for feat_key, feat_value in edge.features.items():
                edge_attr[edge_idx, edge_feature_names.index(feat_key)] = float(feat_value)

        incidence = torch.zeros(
            (len(edge_types), len(self.edges), len(self.nodes)), dtype=torch.float32
        )

        for edge_idx, edge in enumerate(self.edges):
            etype = edge_types.index(type(edge).__name__)
            a_idx = self.nodes.index(edge.node_a)
            b_idx = self.nodes.index(edge.node_b)

            if edge.oriented:
                incidence[etype, edge_idx, a_idx] = -1.0
                incidence[etype, edge_idx, b_idx] = 1.0
            else:
                incidence[etype, edge_idx, a_idx] = 1.0
                incidence[etype, edge_idx, b_idx] = 1.0

        return HouseTensorDTO(
            node_attr=node_attr,
            edge_attr=edge_attr,
            node_type=node_type,
            edge_type=edge_type,
            incidence=incidence,
        )

    def to_json(self, indent: int = 2) -> HouseGraphDTO :
        """Serialize the house graph into a JSON string for visualization.

        Output format:
          - nodes: [{id, type, features}, ...]
          - edges: [{source, target, oriented, features}, ...]

        Node IDs are Python object ids to keep them stable and unique.
        """

        nodes = [
            {
                "id": id(node),
                "type": type(node).__name__,
                "features": node.features,
            }
            for node in self.nodes
        ]

        edges = [
            {
                "source": id(edge.node_a),
                "target": id(edge.node_b),
                "type": type(edge).__name__,
                "oriented": edge.oriented,
                "features": edge.features,
            }
            for edge in self.edges
        ]
        return HouseGraphDTO(nodes=nodes, edges=edges)
