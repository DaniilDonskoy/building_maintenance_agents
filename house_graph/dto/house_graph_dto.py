from __future__ import annotations

from typing import List
from pydantic import BaseModel

from .node_dto import NodeDTO
from .edge_dto import EdgeDTO


class HouseGraphDTO(BaseModel):
    x: int
    y: int
    nodes: List[NodeDTO]
    edges: List[EdgeDTO]
