from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, FLAT_SPACING


@dataclass(slots=True)
class RiserNode(BaseNode):
    def __init__(self, section: int, floor: int, riser_index: int, section_spacing: float):
        section = float(section)
        floor = float(floor)
        riser_index = float(riser_index)
        self.features = {
            "section": section,
            "floor": floor,
            "riser_index": riser_index,
        }
        section_x = (section - 1) * section_spacing
        self.features['x'] = section_x + FLAT_SPACING * (riser_index - 1)
        self.features['y'] = 3.0
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT
