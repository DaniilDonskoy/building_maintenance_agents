from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT
from ..states import IncidentState


@dataclass(slots=True)
class TechNode(BaseNode):
    def __init__(self, sections: int, section_spacing: float):
        sections = float(sections)
        self.features = {
            "sections": sections,
        }
        sections = self.features['sections']
        center_x = (sections - 1) * section_spacing / 2
        self.features['x'] = center_x
        self.features['y'] = -6.0
        self.features['z'] = -FLOOR_HEIGHT
        self.incident_state = IncidentState(has_incident=False, message="")
