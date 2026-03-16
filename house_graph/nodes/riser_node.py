from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, SECTION_SPACING, APARTMENT_SPACING


@dataclass(slots=True)
class RiserNode(BaseNode):
    def __init__(self, section: int, floor: int, apartment_index: int, apartments_per_section: int):
        self.features = {
            "section": float(section),
            "floor": float(floor),
            "apartment_index": float(apartment_index),
            "apartments_per_section": float(apartments_per_section),
        }
        self.__post_init__()

    def __post_init__(self) -> None:
        if any(key not in self.features for key in ("section", "floor", "apartment_index", "apartments_per_section")):
            raise ValueError("RiserNode requires 'section', 'floor', 'apartment_index', and 'apartments_per_section' in features")
        section = self.features['section']
        floor = self.features['floor']
        apartment_index = self.features['apartment_index']
        apartments_per_section = self.features['apartments_per_section']
        section_x = (section - 1) * SECTION_SPACING
        riser_x = section_x + (apartment_index - (apartments_per_section + 1) / 2) * APARTMENT_SPACING
        self.features['x'] = riser_x
        self.features['y'] = 3.0
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT