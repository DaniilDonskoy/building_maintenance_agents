from __future__ import annotations

from typing import Dict
from pydantic import BaseModel


class NodeDTO(BaseModel):
    id: int
    type: str
    features: Dict[str, float]
