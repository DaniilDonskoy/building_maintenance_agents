from pydantic import BaseModel, Field
from typing import Optional, List, Literal

from house_graph import HouseGraphDTO


class HouseConstructorParams(BaseModel):
    house_type: Optional[Literal['House15', 'House16', 'House27']] = Field(None, description="House type")
    floors: Optional[int] = Field(description="Number of floors")
    sections: Optional[int] = Field(description="Number of sections")
    flats_per_section: Optional[int] = Field(description="Number of apartments per section")
    elevs_per_section: Optional[int] = Field(description="Number of elevators per section")
    x: Optional[int] = Field(description="X coordinate")
    y: Optional[int] = Field(description="Y coordinate")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "floors": 15,
                    "sections": 2,
                    "flats_per_section": 3,
                    "elevs_per_section": 1,
                    "x": 0,
                    "y": 0,
                },
                {
                    "house_type": "House16",
                },
            ]
        }


class ComplexConstructorParams(BaseModel):
    total_houses: Optional[int] = Field(ge=1, le=100, description="Number of houses in the complex")
    houses: Optional[List[HouseConstructorParams]] = Field(None, description="Optional parameters for each house")

    class Config:
        json_schema_extra = {
            "example": {
                "total_houses": 5,
            }
        }


class ComplexResponse(BaseModel):
    houses: List[HouseGraphDTO] = Field(..., description="List of houses in the complex")
    total_houses_count: int = Field(..., description="Total number of houses in the complex")

    class Config:
        json_schema_extra = {
            "example": {
                "houses": [
                    {
                        "x": 100.5,
                        "y": 200.3,
                        "nodes": [],
                        "edges": [],
                    }
                ],
                "total_houses_count": 5,
            }
        }
