from __future__ import annotations
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
        pass
        