from fastapi import APIRouter
from loguru import logger
from random import uniform

from house_graph import HouseFactory, HouseGraphDTO

from ....schemas import HouseConstructorParams, ComplexConstructorParams, ComplexResponse


router = APIRouter()

HOUSE_WIDTH = 10.0


def _houses_collide(h1, h2):
    return not (h1.x + h1.length <= h2.x or
                h2.x + h2.length <= h1.x or
                h1.y + HOUSE_WIDTH <= h2.y or
                h2.y + HOUSE_WIDTH <= h1.y)


@router.post('/house/', response_model=HouseGraphDTO)
async def create_house(params: HouseConstructorParams) -> HouseGraphDTO:
    class DynamicHouseFactory(HouseFactory):
        floors = params.floors
        sections = params.sections
        flats_per_section = params.flats_per_section
        elevs_per_section = params.elevs_per_section
    house = DynamicHouseFactory.build(x=params.x or 0, y=params.y or 0)
    return house.to_json()


@router.post('/complex/', response_model=ComplexResponse)
async def create_complex(params: ComplexConstructorParams) -> ComplexResponse:
    if not params.houses:
        raise ValueError("Houses parameters must be provided")
    
    complex_houses = []
    max_attempts = 100
    
    for house_params in params.houses:
        attempts = 0
        placed = False
        
        while attempts < max_attempts and not placed:
            x = int(uniform(0, 1000))
            y = int(uniform(0, 1000))
            
            class DynamicHouseFactory(HouseFactory):
                floors = house_params.floors
                sections = house_params.sections
                flats_per_section = house_params.flats_per_section
                elevs_per_section = house_params.elevs_per_section
            
            house = DynamicHouseFactory.build(x=x, y=y)
            
            collides = False
            for existing in complex_houses:
                if _houses_collide(house, existing):
                    collides = True
                    break
            
            if not collides:
                complex_houses.append(house)
                placed = True
            
            attempts += 1
    
    return ComplexResponse(
        houses=[house.to_json() for house in complex_houses],
    )
