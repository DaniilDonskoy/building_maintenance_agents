from fastapi import APIRouter
from loguru import logger
from typing import Dict
from random import choice as random_choice, uniform

from house_graph import HouseFactory, HouseGraphDTO
from house_graph.samples import House15Factory, House16Factory, House27Factory
from housing_complex import ComplexFactory

from ....schemas import HouseConstructorParams, ComplexConstructorParams, ComplexResponse


router = APIRouter()

HOUSE_TYPE_FACTORIES: Dict[str, type] = {
    "House15": House15Factory,
    "House16": House16Factory,
    "House27": House27Factory,
}


@router.post('/house/', response_model=HouseGraphDTO)
async def create_house(params: HouseConstructorParams) -> HouseGraphDTO:
    if params.house_type is not None:
        factory_cls = HOUSE_TYPE_FACTORIES.get(params.house_type)
        if factory_cls is None:
            raise ValueError(f"Invalid house type: {params.house_type}")
        return factory_cls.build(x=params.x, y=params.y).to_json()
    
    class DynamicHouseFactory(HouseFactory):
        floors = params.floors
        sections = params.sections
        flats_per_section = params.flats_per_section
        elevs_per_section = params.elevs_per_section
    house = DynamicHouseFactory.build(x=params.x, y=params.y)
    return house.to_json()


@router.post('/complex/', response_model=ComplexResponse)
async def create_complex(params: ComplexConstructorParams) -> ComplexResponse:
        
    complex_houses = []
    HOUSE_WIDTH = 10.0
    max_attempts = 100
    
    if params.houses:
        complex_houses = [
            await create_house(house_params) for house_params in params.houses
        ]
    else:
        complex_houses = ComplexFactory.build(total_houses=params.total_houses).houses
    
    houses_json = [house.to_json() for house in complex_houses]        
    return ComplexResponse(
        houses=houses_json,
        total_houses_count=len(complex_houses),
    )
