from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict
from ..nodes import BaseNode


@dataclass(slots=True)
class BaseEdge:
    node_a: BaseNode
    node_b: BaseNode
    features: Dict[str, float] = field(default_factory=dict)

    @property
    def oriented(self) -> bool:
        return bool(self.features.get("oriented"))
    
    @property
    def horisontal(self) -> bool:
        return bool(self.features.get("horizontal"))
    
    @property
    def vertical(self) -> bool:
        return bool(self.features.get("vertical"))