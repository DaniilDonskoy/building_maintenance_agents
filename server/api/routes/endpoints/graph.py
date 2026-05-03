from fastapi import APIRouter, FastAPI, UploadFile, File

from loguru import logger
from typing import Dict, Literal

from house_graph import HouseFactory, HouseGraphDTO
from house_graph.samples import House15Factory, House16Factory, House27Factory

# import pandas as pd # use pandas for excel files

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


# ---------------------------------------- Move to another routes: incidents-file (route), schedule (route) -------

# @router.post('/incidents-file/')
# async def post_excel_file(file: UploadFile) -> pd.DataFrame:
#     file_df = pd.read_excel(file)
    
#     # pip install python-multipart
#     # TODO: fill this method
    
#     return file_df # return pandas dataframe


# @router.get('/schedule/')
# async def get_schedule_excel_file():
#     # when we will generate schedule
#     excel_file = ...
#     return excel_file