from __future__ import annotations

from .edges import PathEdge, ElecEdge, HotWaterEdge, ColdWaterEdge
from .house import House
from .nodes import ElecNode, ElevNode, FlatNode, MopNode, RiserNode, TechNode


class HouseFactory:
    floors: int = 2
    sections: int = 1
    flats_per_section: int = 1
    elevs_per_section: int = 1

    @classmethod
    def build(cls) -> House:
        house = House()
        tech_node = TechNode(sections=cls.sections)
        house.add_node(tech_node)
        for section in range(1, cls.sections + 1):
            last_mop_node = tech_node
            last_elec_node = tech_node
            last_elev_nodes = [None] * cls.elevs_per_section
            last_riser_nodes = [tech_node] * cls.flats_per_section
            for floor in range(1, cls.floors + 1):
                elec_node = ElecNode(section=section, floor=floor)
                house.add_node(elec_node)
                house.add_edge(ElecEdge(last_elec_node, elec_node, vertical=True))
                last_elec_node = elec_node
                mop_node = MopNode(section=section, floor=floor)
                house.add_node(mop_node)
                house.add_edge(PathEdge(last_mop_node, mop_node, vertical=True))
                last_mop_node = mop_node
                house.add_edge(PathEdge(mop_node, elec_node, horizontal=True))
                for elev_idx in range(1, cls.elevs_per_section + 1):
                    elev_node = ElevNode(section=section, floor=floor, elev_index=elev_idx)
                    house.add_node(elev_node)
                    house.add_edge(PathEdge(elev_node, mop_node, horizontal=True))
                    if last_elev_nodes[elev_idx - 1] is not None:
                        house.add_edge(PathEdge(elev_node, last_elev_nodes[elev_idx - 1], vertical=True))
                    last_elev_nodes[elev_idx - 1] = elev_node
                for flat_idx in range(1, cls.flats_per_section + 1):
                    flat_node = FlatNode(section=section, floor=floor, flat_index=flat_idx, flats_per_section=cls.flats_per_section)
                    house.add_node(flat_node)
                    house.add_edge(PathEdge(flat_node, mop_node, horizontal=True))
                    house.add_edge(ElecEdge(elec_node, flat_node, horizontal=True))
                    riser_node = RiserNode(section=section, floor=floor, flat_index=flat_idx, flats_per_section=cls.flats_per_section)
                    house.add_node(riser_node)
                    for edge_type in (HotWaterEdge, ColdWaterEdge):
                        house.add_edge(edge_type(riser_node, flat_node, horizontal=True))
                        house.add_edge(edge_type(last_riser_nodes[flat_idx - 1], riser_node, vertical=True))
                    last_riser_nodes[flat_idx - 1] = riser_node

        for edge in house.edges:
            node_a = edge.node_a
            node_b = edge.node_b
            node_a.features["degree"] = node_a.features.get("degree", 0) + 1
            node_b.features["degree"] = node_b.features.get("degree", 0) + 1
        return house