from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT, SECTION_SPACING, APARTMENT_SPACING


@dataclass(slots=True)
class FlatNode(BaseNode):
    def __post_init__(self) -> None:
        super().__post_init__()
        if any(key not in self.features for key in ("section", "floor", "apartment_index", "apartments_per_section")):
            raise ValueError("FlatNode requires 'section', 'floor', 'apartment_index', and 'apartments_per_section' in features")
        section = self.features['section']
        floor = self.features['floor']
        apartment_index = self.features['apartment_index']
        apartments_per_section = self.features['apartments_per_section']
        section_x = (section - 1) * SECTION_SPACING
        apt_x = section_x + (apartment_index - (apartments_per_section + 1) / 2) * APARTMENT_SPACING
        self.features['x'] = apt_x
        self.features['y'] = 6.0
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT