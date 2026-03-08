from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import torch


NODE_TYPES = ("APT", "MOP", "LIFT", "RISER", "PANEL", "ITP", "TECH", "ROOF")
EDGE_TYPES = ("ADJ", "HEAT", "COLD", "HOT", "ELEC", "VENT", "DRAIN")


@dataclass(slots=True)
class Node:
    id: str
    type: str
    features: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in NODE_TYPES:
            raise ValueError(f"Unknown node type: {self.type}")
        self.features = {k: float(v) for k, v in self.features.items()}


@dataclass(slots=True)
class Edge:
    id: str
    type: str
    node_ids: List[str]

    def __post_init__(self) -> None:
        if self.type not in EDGE_TYPES:
            raise ValueError(f"Unknown edge type: {self.type}")
        if len(self.node_ids) < 2:
            raise ValueError("Edge must connect at least two nodes")


@dataclass
class House:
    id: str
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        if any(n.id == node.id for n in self.nodes):
            raise ValueError(f"Duplicate node id: {node.id}")
        self.nodes.append(node)

    def add_edge(self, edge: Edge) -> None:
        node_ids = {n.id for n in self.nodes}
        missing = [nid for nid in edge.node_ids if nid not in node_ids]
        if missing:
            raise ValueError(f"Edge {edge.id} references missing nodes: {missing}")
        if any(e.id == edge.id for e in self.edges):
            raise ValueError(f"Duplicate edge id: {edge.id}")
        self.edges.append(edge)

    def to_tensors(self) -> dict:
        node_index = {node.id: i for i, node in enumerate(self.nodes)}
        edge_index = {edge.id: i for i, edge in enumerate(self.edges)}
        edge_type_index = {etype: i for i, etype in enumerate(EDGE_TYPES)}

        feature_names = sorted({name for n in self.nodes for name in n.features})
        x = torch.zeros((len(self.nodes), len(feature_names)), dtype=torch.float32)
        for i, node in enumerate(self.nodes):
            for j, name in enumerate(feature_names):
                if name in node.features:
                    x[i, j] = node.features[name]

        node_type = torch.zeros((len(self.nodes), len(NODE_TYPES)), dtype=torch.float32)
        for i, node in enumerate(self.nodes):
            node_type[i, NODE_TYPES.index(node.type)] = 1.0

        incidence = torch.zeros(
            (len(EDGE_TYPES), len(self.edges), len(self.nodes)), dtype=torch.float32
        )
        for e_idx, edge in enumerate(self.edges):
            t_idx = edge_type_index[edge.type]
            for node_id in edge.node_ids:
                n_idx = node_index[node_id]
                incidence[t_idx, e_idx, n_idx] = 1.0

        return {
            # Набор признаков для каждого узла (размер: num_nodes x num_features)
            "x": x,
            # One-hot кодирование типа узла (размер: num_nodes x num_node_types)
            "node_type": node_type,
            # Инцидентная матрица (размер: num_edge_types x num_edges x num_nodes)
            "incidence": incidence,
            # Списки идентификаторов узлов и рёбер для удобства (index = идентификатор)
            "node_ids": list(node_index.keys()),
            "edge_ids": list(edge_index.keys()),
            # Список названий признаков для удобства
            "feature_names": feature_names,
        }


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


if __name__ == "__main__":
    house = HouseFactory.build("house_1", floors=2, apartments_per_floor=2)
    # А тут можно будет добавить доп. параметры, описывающие состояние узлов и рёбер, например, температуру, давление, статус неисправности и т.д.
    # Пока из характеристик есть только этаж (а нужно ли больше?)
    tensors = house.to_tensors()
    for name, value in tensors.items():
        print(f"{name}: {value}")