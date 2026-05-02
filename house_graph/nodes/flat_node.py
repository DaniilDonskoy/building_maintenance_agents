from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, FLAT_SPACING


@dataclass(slots=True)
class FlatNode(BaseNode):
    def __init__(self, section: int, floor: int, flat_index: int, section_spacing: float):
        section = float(section)
        floor = float(floor)
        flat_index = float(flat_index)
        self.features = {
            "section": section,
            "floor": floor,
            "flat_index": flat_index,
        }
        section_x = (section - 1) * section_spacing
        self.features['x'] = section_x + FLAT_SPACING * (flat_index - 1)
        self.features['y'] = 6.0
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT
