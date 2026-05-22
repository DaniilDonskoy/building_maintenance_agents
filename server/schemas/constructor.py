from pydantic import BaseModel, Field
from typing import Optional, List, Literal

from house_graph import HouseGraphDTO


class HouseConstructorParams(BaseModel):
    floors: int = Field(description="Number of floors")
    sections: int = Field(description="Number of sections")
    flats_per_section: int = Field(description="Number of apartments per section")
    elevs_per_section: int = Field(description="Number of elevators per section")
    street: Optional[str] = Field(None, description="Street name (optional)")
    number: Optional[str] = Field(None, description="House number (optional)")
    x: Optional[int] = Field(0, description="X coordinate")
    y: Optional[int] = Field(0, description="Y coordinate")

    class Config:
        json_schema_extra = {
            "example": {
                "floors": 15,
                "sections": 2,
                "flats_per_section": 3,
                "elevs_per_section": 1,
                "street": "ул. Пушкина",
                "number": "12с1",
            }
        }


class ComplexConstructorParams(BaseModel):
    houses: Optional[List[HouseConstructorParams]] = Field(None, description="Optional parameters for each house")

    class Config:
        json_schema_extra = {
            "example": {
                "houses": [
                    {
                        "floors": 15,
                        "sections": 2,
                        "flats_per_section": 3,
                        "elevs_per_section": 1,
                        "street": "ул. Пушкина",
                        "number": "12с1",
                    },
                    {
                        "floors": 10,
                        "sections": 1,
                        "flats_per_section": 4,
                        "elevs_per_section": 2,
                        "street": "ул. Ленина",
                        "number": "5",
                    },
                ]
            }
        }


class ComplexResponse(BaseModel):
    houses: List[HouseGraphDTO] = Field(..., description="List of houses in the complex")

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
            }
        }
