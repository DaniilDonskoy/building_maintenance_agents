from fastapi import APIRouter
from loguru import logger

from ....schemas import GraphParams


router = APIRouter()


@router.get('/')
async def get_building_graph(graph_params: GraphParams) -> dict:
    logger.debug("Get list of admins")
    return ...


# TO ADD:

# from typing import Dict
# from fastapi import FastAPI, HTTPException
# from fastapi.responses import Response
# from house_graph.samples import House15Factory, House16Factory, House27Factory
# from house_graph.house_factory import HouseFactory

# app = FastAPI()

# factories: Dict[str, HouseFactory] = {
#     "House15": House15Factory,
#     "House16": House16Factory,
#     "House27": House27Factory,
# }

# @app.get("/get_graph", responses={200: {"content": {"application/json": {}}}})
# def get_graph(house_type: str = "House15") -> Response:
#     factory = factories.get(house_type)
#     if factory is None:
#         raise HTTPException(status_code=400, detail="Invalid house type")
#     house = factory.build()
#     return Response(content=house.to_json(), media_type="application/json")
