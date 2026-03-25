from typing import Dict

from .flow_edge import FlowEdge
from ..nodes import BaseNode


class HotWaterEdge(FlowEdge):
    def __init__(
            self,
            node_a: BaseNode,
            node_b: BaseNode,
            vertical: bool = False,
            horizontal: bool = False,
            features: Dict[str, float] = {}
            ):
        super().__init__(node_a, node_b, vertical, horizontal, features)