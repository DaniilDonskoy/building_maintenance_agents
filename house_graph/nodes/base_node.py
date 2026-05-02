from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ..states import IncidentState


FLOOR_HEIGHT = 3.0
FLAT_SPACING = 6.0


@dataclass(slots=True)
class BaseNode:
    features: Dict[str, float] = field(default_factory=dict)
    incident_state: IncidentState = field(default_factory=IncidentState)
