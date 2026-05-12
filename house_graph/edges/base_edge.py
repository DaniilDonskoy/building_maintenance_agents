from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ..nodes import BaseNode
from ..states import IncidentState


@dataclass(slots=True)
class BaseEdge:
    node_a: BaseNode
    node_b: BaseNode
    features: Dict[str, float] = field(default_factory=dict)
    incident_state: IncidentState = field(default_factory=IncidentState)
    house: None = field(default=None)

    @property
    def oriented(self) -> bool:
        return bool(self.features.get("oriented"))
    
    @property
    def horisontal(self) -> bool:
        return bool(self.features.get("horizontal"))
    
    @property
    def vertical(self) -> bool:
        return bool(self.features.get("vertical"))