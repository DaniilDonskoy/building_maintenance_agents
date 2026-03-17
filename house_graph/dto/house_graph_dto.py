from __future__ import annotations

from typing import List
from pydantic import BaseModel

from .node_dto import NodeDTO
from .edge_dto import EdgeDTO


class HouseGraphDTO(BaseModel):
    nodes: List[NodeDTO]
    edges: List[EdgeDTO]
