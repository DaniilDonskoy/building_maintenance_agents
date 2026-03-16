from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from .base_edge import BaseEdge
from ..nodes import BaseNode


@dataclass(slots=True)
class PathEdge(BaseEdge):
    def __init__(self, node_a: BaseNode, node_b: BaseNode, features: Dict[str, float] = {}):
        self.node_a = node_a
        self.node_b = node_b
        self.features = {**features, "oriented": 0.0}