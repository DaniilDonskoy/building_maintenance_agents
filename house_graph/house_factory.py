from __future__ import annotations

from typing import Dict, Optional

from .edges import FlowEdge, PathEdge
from .house import House
from .nodes import ElecNode, ElevNode, FlatNode, MopNode, RiserNode, TechNode


class HouseFactory:
    """Builds a house graph given high-level configuration.

    The generated graph follows the structure from the provided schema:
      - Path edges: connect flats to corridors (mop), corridors across floors (stairs), and lifts to corridors.
      - Flow edges: connect the technical node (ITP) to risers on the first floor, risers between floors, and risers to apartments.
    """

    floors: int = 2
    sections: int = 1
    apartments_per_section: int = 1
    lifts_per_section: int = 1

    @classmethod
    def build(cls, house_id: str) -> House:
        house = House()
        tech_node = TechNode(sections=cls.sections)
        house.add_node(tech_node)
        for section in range(1, cls.sections + 1):
            for floor in range(1, cls.floors + 1):
                elec_node = ElecNode(section=section, floor=floor)
                house.add_node(elec_node)
                mop_node = MopNode(section=section, floor=floor)
                house.add_node(mop_node)
                house.add_edge(PathEdge(mop_node, tech_node, horizontal=True))
                