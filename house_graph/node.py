from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


NODE_TYPES = ("APT", "MOP", "LIFT", "RISER", "PANEL", "ITP", "TECH", "ROOF")


@dataclass(slots=True)
class Node:
    id: str
    type: str
    features: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in NODE_TYPES:
            raise ValueError(f"Unknown node type: {self.type}")
        self.features = {k: float(v) for k, v in self.features.items()}