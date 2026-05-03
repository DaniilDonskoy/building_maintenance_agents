from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict
from .base_edge import BaseEdge
from ..nodes import BaseNode
from ..states import IncidentState


@dataclass(slots=True)
class FlowEdge(BaseEdge):
    def __init__(
            self,
            node_a: BaseNode,
            node_b: BaseNode,
            vertical: bool = False,
            horizontal: bool = False,
            features: Dict[str, float] = field(default_factory=dict)
        ) -> None:
        self.node_a = node_a
        self.node_b = node_b
        self.features = {
            "oriented": 1.0,
            "vertical": float(vertical),
            "horizontal": float(horizontal),
            **features
        }
        self.incident_state = IncidentState(has_incident=False, message="")