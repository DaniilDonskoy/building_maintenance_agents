from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

import torch

from dto import HouseTensorDTO
from .edge import EDGE_TYPES, Edge
from .node import NODE_TYPES, Node


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

    def to_tensors(self) -> HouseTensorDTO:
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

        return HouseTensorDTO(
            x=x,
            node_type=node_type,
            incidence=incidence,
            node_ids=list(node_index.keys()),
            edge_ids=list(edge_index.keys()),
            feature_names=feature_names,
        )
        