from __future__ import annotations

from typing import Dict
from pydantic import BaseModel


class EdgeDTO(BaseModel):
    source: int
    target: int
    type: str
    oriented: bool
    features: Dict[str, float]
