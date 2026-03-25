from pydantic import BaseModel, Field
from typing import Literal


class GraphParams(BaseModel):
    floors: int = Field(description="Number of floors in the building", examples=[15, 16, 27])
    sections: int = Field(description="Number of sections in the building", examples=[2, 3, 4])
    flats_per_section: int = Field(description="Number of flats per section", examples=[2, 3, 4])
    elevs_per_section: int = Field(description="Number of elevators per section", examples=[1, 2, 4])

class GraphType(BaseModel):
    type: Literal['House15', 'House16', 'House27'] = Field(description="Type of the building graph", examples=['House15', 'House16', 'House27'])