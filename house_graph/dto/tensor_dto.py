from dataclasses import dataclass
from typing import List
import torch


@dataclass(slots=True)
class HouseTensorDTO:
    node_attr: torch.Tensor   # Набор признаков для каждого узла (размер: num_nodes x num_features)
    edge_attr: torch.Tensor   # Набор признаков для каждого ребра (размер: num_edges x num_edge_features)
    node_type: torch.Tensor   # One-hot кодирование типа узла (размер: num_nodes x num_node_types)
    edge_type: torch.Tensor   # One-hot кодирование типа ребра (размер: num_edges x num_edge_types)
    incidence: torch.Tensor   # Инцидентная матрица (размер: num_edge_types x num_edges x num_nodes)
