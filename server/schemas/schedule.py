from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class TaskDTO(BaseModel):
    id: int = Field(None, description="Идентификатор задачи")
    agent: str = Field(None, description="Агент")
    time: datetime = Field(None, description="Время")
    building: str = Field(None, description="Здание")
    node: str = Field(None, description="Узел")
    cost: float = Field(None, description="Стоимость")


class ScheduleDTO(BaseModel):
    tasks: List[TaskDTO] = Field(description="Список задач/планов работ")


class ScheduleResponse(ScheduleDTO):
    pass