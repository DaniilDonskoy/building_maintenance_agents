from fastapi import APIRouter

from .routes.endpoints import graph_router, incidents_router, schedule_router, constructor_router

router = APIRouter()
router.include_router(graph_router, tags=["graph"], prefix="/graph")
router.include_router(incidents_router, tags=["incidents"], prefix="/incidents-file")
router.include_router(schedule_router, tags=["schedule"], prefix="/schedule")
router.include_router(constructor_router, tags=["constructor"], prefix="/constructor")
