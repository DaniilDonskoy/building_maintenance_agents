from __future__ import annotations

from .edge import Edge
from .house import House
from .node import Node


class HouseFactory:
    @staticmethod
    def build(
        house_id: str,
        floors: int = 10,
        apartments_per_floor: int = 2,
        lifts: int = 1,
        risers: int = 1,
    ) -> House:
        house = House(id=house_id)
        # Добавляем базовые узлы: ИТП, Техпомещение, Крыша
        house.add_node(Node("itp_1", "ITP", {"floor": 0}))
        house.add_node(Node("tech_1", "TECH", {"floor": 0}))
        house.add_node(Node("roof_1", "ROOF", {"floor": floors + 1}))

        # На каждый этаж добавляем МОП, Элекктрощит
        for floor in range(1, floors + 1):
            mop_id = f"mop_{floor}"
            panel_id = f"panel_{floor}"
            house.add_node(Node(mop_id, "MOP", {"floor": floor}))
            house.add_node(Node(panel_id, "PANEL", {"floor": floor}))

            apt_ids = []
            lift_ids = []
            riser_ids = []

            # На каждый этаж добавляем квартиры, лифты и стояки
            for i in range(1, apartments_per_floor + 1):
                apt_id = f"apt_{floor}_{i}"
                apt_ids.append(apt_id)
                house.add_node(Node(apt_id, "APT", {"floor": floor}))

            for i in range(1, lifts + 1):
                lift_id = f"lift_{floor}_{i}"
                lift_ids.append(lift_id)
                house.add_node(Node(lift_id, "LIFT", {"floor": floor}))

            for i in range(1, risers + 1):
                riser_id = f"riser_{floor}_{i}"
                riser_ids.append(riser_id)
                house.add_node(Node(riser_id, "RISER", {"floor": floor}))

            # Добавляем рёбра между МОП, Электрощитом, Квартирами, Лифтом, Стояком, ИТП, Техпомещением и Крышей
            house.add_edge(Edge(f"adj_{floor}", "ADJ", [mop_id, *apt_ids, *lift_ids, *riser_ids]))
            house.add_edge(Edge(f"elec_{floor}", "ELEC", [panel_id, *apt_ids, *lift_ids]))
            house.add_edge(Edge(f"vent_{floor}", "VENT", ["tech_1", *apt_ids, "roof_1"]))

            # Рёбра для отопления, холодного и горячего водоснабжения, а также канализации
            # Исходя из количества стояков, распределяем квартиры по ним равномерно
            for i, riser_id in enumerate(riser_ids, start=1):
                attached_apts = apt_ids[i - 1 :: len(riser_ids)]
                if attached_apts:
                    house.add_edge(Edge(f"heat_{floor}_{i}", "HEAT", ["itp_1", riser_id, *attached_apts]))
                    house.add_edge(Edge(f"cold_{floor}_{i}", "COLD", [riser_id, *attached_apts]))
                    house.add_edge(Edge(f"hot_{floor}_{i}", "HOT", ["itp_1", riser_id, *attached_apts]))
                    house.add_edge(Edge(f"drain_{floor}_{i}", "DRAIN", [riser_id, *attached_apts, "tech_1"]))

        return house
