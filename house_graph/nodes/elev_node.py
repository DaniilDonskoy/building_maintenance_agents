from __future__ import annotations

from dataclasses import dataclass
from .base_node import BaseNode, FLOOR_HEIGHT
from ..states import IncidentState


@dataclass(slots=True)
class ElevNode(BaseNode):
    def __init__(self, section: int, floor: int, elev_index: int, section_spacing: float):
        section = float(section)
        floor = float(floor)
        elev_index = float(elev_index)
        self.features = {
            "section": section,
            "floor": floor,
            "elev_index": elev_index,
        }
        section_x = (section - 1) * section_spacing
        self.features['x'] = section_x + 1.5 * (elev_index - 1)
        self.features['y'] = 1.5
        self.features['z'] = (floor - 1) * FLOOR_HEIGHT
        self.incident_state = IncidentState(has_incident=False, message="")
