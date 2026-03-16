from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, SECTION_SPACING


@dataclass(slots=True)
class ElecNode(BaseNode):
    def __init__(self, section: int, floor: int):
        self.features = {
            "section": float(section),
            "floor": float(floor),
        }
        self.__post_init__()

    def __post_init__(self) -> None:
        if any(key not in self.features for key in ("section", "floor")):
            raise ValueError("ElecNode requires 'section' and 'floor' in features")
        section = self.features['section']
        floor = self.features['floor']
        self.features['x'] = (section - 1) * SECTION_SPACING - 3.0
        self.features['y'] = -2.0
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT