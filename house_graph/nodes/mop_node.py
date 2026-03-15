from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, SECTION_SPACING


@dataclass(slots=True)
class MopNode(BaseNode):
    def __post_init__(self) -> None:
        super().__post_init__()
        if any(key not in self.features for key in ("section", "floor")):
            raise ValueError("MopNode requires 'section' and 'floor' in features")
        self.features['x'] = (self.features['section'] - 1) * SECTION_SPACING
        self.features['y'] = 0.0
        self.features['z'] = (self.features['floor'] - 1) * FLOOR_HEIGHT