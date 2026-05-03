from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT
from ..states import IncidentState


@dataclass(slots=True)
class MopNode(BaseNode):
    def __init__(self, section: int, floor: int, section_spacing: float):
        section = float(section)
        floor = float(floor)
        self.features = {
            "section": section,
            "floor": floor,
        }
        self.features['x'] = (section - 1) * section_spacing
        self.features['y'] = 0.0
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT
        self.incident_state = IncidentState(has_incident=False, message="")
