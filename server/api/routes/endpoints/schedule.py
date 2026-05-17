from fastapi import APIRouter
from ....schemas import ScheduleResponse

router = APIRouter()


@router.get('/', response_model=ScheduleResponse)
async def get_schedule():
    from datetime import datetime, timedelta
    tasks = [
        {
            "id": 1,
            "agent": "Бригада 1",
            "time": datetime.now(),
            "building": "18-этажный дом, ЖК Солнечный",
            "node": "ГВС 1",
            "cost": 24500.0,
        },
        {
            "id": 2,
            "agent": "Бригада 2",
            "time": datetime.now() + timedelta(hours=1),
            "building": "12-этажный дом, ЖК Ривьера",
            "node": "ГВС 2",
            "cost": 31200.0,
        },
    ]

    return ScheduleResponse(
        tasks=tasks,
    )
