from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, SECTION_SPACING, FLAT_SPACING


@dataclass(slots=True)
class FlatNode(BaseNode):
    def __init__(self, section: int, floor: int, flat_index: int, flats_per_section: int):
        self.features = {
            "section": float(section),
            "floor": float(floor),
            "flat_index": float(flat_index),
            "flats_per_section": float(flats_per_section),
        }
        self.__post_init__()

    def __post_init__(self) -> None:
        if any(key not in self.features for key in ("section", "floor", "flat_index", "flats_per_section")):
            raise ValueError("FlatNode requires 'section', 'floor', 'flat_index', and 'flats_per_section' in features")
        section = self.features['section']
        floor = self.features['floor']
        flat_index = self.features['flat_index']
        flats_per_section = self.features['flats_per_section']
        section_x = (section - 1) * SECTION_SPACING
        apt_x = section_x + (flat_index - (flats_per_section + 1) / 2) * FLAT_SPACING
        self.features['x'] = apt_x
        self.features['y'] = 6.0
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT