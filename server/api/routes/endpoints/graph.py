from fastapi import APIRouter
from loguru import logger
from typing import Dict, Literal

from house_graph import HouseFactory, HouseGraphDTO
from house_graph.samples import House15Factory, House16Factory, House27Factory

from ....schemas import GraphType


router = APIRouter()


factories: Dict[str, HouseFactory] = {
    "House15": House15Factory,
    "House16": House16Factory,
    "House27": House27Factory,
}


@router.get('/')
async def get_building_graph(graph_type: Literal["House15", "House16", "House27"]) -> HouseGraphDTO:
    # logger.debug("Get list of admins")
    factory = factories.get(graph_type)
    if factory is None:
        logger.error(f"Invalid graph type: {graph_type}")
        return None
    house = factory.build()
    return house.to_json()
