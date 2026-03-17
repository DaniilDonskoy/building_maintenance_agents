from __future__ import annotations

import torch
from dataclasses import dataclass, field
from typing import List

from .dto import HouseTensorDTO
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
            for key in node.features.keys()
        })

        node_attr = torch.zeros((len(self.nodes), len(node_feature_names)), dtype=torch.float32)
        for node_idx, node in enumerate(self.nodes):
            for feat_idx, feat_name in enumerate(node_feature_names):
                node_attr[node_idx, feat_idx] = float(node.features.get(feat_name, 0.0))

        node_type_to_idx: dict[str, int] = {}
        node_type_indices: list[int] = []
        for node in self.nodes:
            node_type = type(node).__name__
            if node_type not in node_type_to_idx:
                node_type_to_idx[node_type] = len(node_type_to_idx)
            node_type_indices.append(node_type_to_idx[node_type])

        node_type = torch.zeros((len(self.nodes), len(node_type_to_idx)), dtype=torch.float32)
        for node_idx, type_idx in enumerate(node_type_indices):
            node_type[node_idx, type_idx] = 1.0

        node_ids = [f"{type(node).__name__}-{idx}" for idx, node in enumerate(self.nodes)]

        edge_feature_names = sorted({
            key
            for edge in self.edges
            for key in edge.features.keys()
        })

        edge_attr = torch.zeros((len(self.edges), len(edge_feature_names)), dtype=torch.float32)
        for edge_idx, edge in enumerate(self.edges):
            for feat_idx, feat_name in enumerate(edge_feature_names):
                edge_attr[edge_idx, feat_idx] = float(edge.features.get(feat_name, 0.0))

        edge_type_to_idx: dict[str, int] = {}
        edge_type_indices: list[int] = []
        for edge in self.edges:
            edge_type = type(edge).__name__
            if edge_type not in edge_type_to_idx:
                edge_type_to_idx[edge_type] = len(edge_type_to_idx)
            edge_type_indices.append(edge_type_to_idx[edge_type])

        edge_type = torch.zeros((len(self.edges), len(edge_type_to_idx)), dtype=torch.float32)
        for edge_idx, type_idx in enumerate(edge_type_indices):
            edge_type[edge_idx, type_idx] = 1.0

        edge_ids = [f"{type(edge).__name__}-{idx}" for idx, edge in enumerate(self.edges)]

        node_index_by_id = {id(node): idx for idx, node in enumerate(self.nodes)}
        incidence = torch.zeros(
            (len(edge_type_to_idx), len(self.edges), len(self.nodes)), dtype=torch.float32
        )

        for edge_idx, edge in enumerate(self.edges):
            etype = edge_type_to_idx[type(edge).__name__]
            a_idx = node_index_by_id.get(id(edge.node_a))
            b_idx = node_index_by_id.get(id(edge.node_b))
            if a_idx is None or b_idx is None:
                continue

            if getattr(edge, "oriented", False):
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
            node_ids=node_ids,
            edge_ids=edge_ids,
            node_feature_names=node_feature_names,
            edge_feature_names=edge_feature_names,
        )
        