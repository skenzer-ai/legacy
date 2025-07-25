from fastapi import APIRouter

from .endpoints import process, retrieve

api_router = APIRouter()
api_router.include_router(process.router, prefix="/process", tags=["process"])
api_router.include_router(retrieve.router, prefix="/retrieve", tags=["retrieve"])