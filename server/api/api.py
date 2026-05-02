from fastapi import APIRouter

from .routes.endpoints import graph_router

router = APIRouter()
router.include_router(graph_router, tags=["graph"], prefix="/graph")
