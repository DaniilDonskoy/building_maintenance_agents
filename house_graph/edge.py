from __future__ import annotations
from dataclasses import dataclass
from typing import List


EDGE_TYPES = ("ADJ", "HEAT", "COLD", "HOT", "ELEC", "VENT", "DRAIN")


@dataclass(slots=True)
class Edge:
    id: str
    type: str
    node_ids: List[str]

    def __post_init__(self) -> None:
        if self.type not in EDGE_TYPES:
            raise ValueError(f"Unknown edge type: {self.type}")
        if len(self.node_ids) < 2:
            raise ValueError("Edge must connect at least two nodes")
