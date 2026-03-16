from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


FLOOR_HEIGHT = 3.0
SECTION_SPACING = 30.0
FLAT_SPACING = 6.0


@dataclass(slots=True)
class BaseNode:
    features: Dict[str, float] = field(default_factory=dict)
