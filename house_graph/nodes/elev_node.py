from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, SECTION_SPACING


@dataclass(slots=True)
class ElevNode(BaseNode):
    def __init__(self, section: int, floor: int, elev_index: int):
        self.features = {
            "section": float(section),
            "floor": float(floor),
            "elev_index": float(elev_index),
        }
        self.__post_init__()

    def __post_init__(self) -> None:
        if any(key not in self.features for key in ("section", "floor", "elev_index")):
            raise ValueError("ElevNode requires 'section', 'floor', and 'elev_index' in features")
        section = self.features['section']
        floor = self.features['floor']
        elev_index = self.features['elev_index']
        section_x = (section - 1) * SECTION_SPACING
        elev_x = section_x - 2 + 1.5 * (elev_index - 1)
        self.features['x'] = elev_x
        self.features['y'] = 1.5
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT