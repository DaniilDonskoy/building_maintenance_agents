from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IncidentDTO(BaseModel):
    date: Optional[str] = Field(None, description="Дата инцидента")
    time: Optional[str] = Field(None, description="Время инцидента")
    source: Optional[str] = Field(None, description="Источник заявки (Диспетчер, Житель, ...)")
    address: Optional[str] = Field(None, description="Адрес здания")
    room_number: Optional[str] = Field(None, description="Номер помещения")
    category: Optional[str] = Field(None, description="Категория (Аварийная, Плановая, ...)")
    subcategory: Optional[str] = Field(None, description="Подкатегория (Протечка, Электропроводка, ...)")
    description: Optional[str] = Field(None, description="Описание проблемы")
    work_comments: Optional[str] = Field(None, description="Комментарий к выполненным работам")
    status: Optional[str] = Field(None, description="Статус заявки")
    desired_completion_time: Optional[str] = Field(None, description="Желаемое время выполнения")
    execution_date: Optional[str] = Field(None, description="Дата исполнения")
    executors: Optional[str] = Field(None, description="Исполнители")
    coordinators: Optional[str] = Field(None, description="Координаторы")
    materials: Optional[str] = Field(None, description="Перечень материалов")
    services: Optional[str] = Field(None, description="Услуги")
    cost: Optional[float] = Field(None, description="Стоимость")
    attachments: Optional[str] = Field(None, description="Вложения")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "15.03.2026",
                "time": "23:19",
                "source": "Диспетчер",
                "address": "г Санкт-Петербург, п Парголово, ул Николая Рубцова, д. 5 стр. 1",
                "room_number": "309",
                "category": "Аварийная",
                "subcategory": "Протечка",
                "description": "СИЛЬНАЯ ТЕЧЬ СТОЯКА ГВС В ВАННОЙ",
                "work_comments": "Заменили два крана 1/2 на хгвс",
                "status": "Принята к исполнению",
                "cost": 0.0,
                "attachments": "Нет"
            }
        }


class IncidentsResponse(BaseModel):
    total_count: int = Field(description="Total number of incidents")
    incidents: list[IncidentDTO] = Field(description="List of incidents")
