from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, SECTION_SPACING


@dataclass(slots=True)
class TechNode(BaseNode):
    def __init__(self, sections: int):
        self.features = {
            "sections": float(sections),
        }
        self.__post_init__()

    def __post_init__(self) -> None:
        if "sections" not in self.features:
            raise ValueError("TechNode requires 'sections' in features")
        sections = self.features['sections']
        center_x = (sections - 1) * SECTION_SPACING / 2
        self.features['x'] = center_x + 4.0
        self.features['y'] = -6.0
        self.features['z'] = -3.0