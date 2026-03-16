from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, SECTION_SPACING


@dataclass(slots=True)
class ElevNode(BaseNode):
    def __init__(self, section: int, floor: int, lift_index: int):
        self.features = {
            "section": float(section),
            "floor": float(floor),
            "lift_index": float(lift_index),
        }
        self.__post_init__()

    def __post_init__(self) -> None:
        if any(key not in self.features for key in ("section", "floor", "lift_index")):
            raise ValueError("ElevNode requires 'section', 'floor', and 'lift_index' in features")
        section = self.features['section']
        floor = self.features['floor']
        lift_index = self.features['lift_index']
        section_x = (section - 1) * SECTION_SPACING
        lift_x = section_x - 2 + 1.5 * (lift_index - 1)
        self.features['x'] = lift_x
        self.features['y'] = 1.5
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT