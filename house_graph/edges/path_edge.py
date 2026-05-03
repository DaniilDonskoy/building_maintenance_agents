from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from .base_edge import BaseEdge
from ..nodes import BaseNode
from ..states import IncidentState


@dataclass(slots=True)
class PathEdge(BaseEdge):
    def __init__(
            self,
            node_a: BaseNode,
            node_b: BaseNode,
            vertical: bool = False,
            horizontal: bool = False,
            features: Dict[str, float] = {}
        ) -> None:
        self.node_a = node_a
        self.node_b = node_b
        self.features = {
            "oriented": 0.0,
            "vertical": float(vertical),
            "horizontal": float(horizontal),
            **features
        }
        self.incident_state = IncidentState(has_incident=False, message="")