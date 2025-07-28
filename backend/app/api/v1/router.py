from fastapi import APIRouter

from .endpoints import process, retrieve, agents, proxy, auth, users, tasks
from ...core.manoman.api import classification, definition, upload, status, validation, services

api_router = APIRouter()

# Authentication & User Management
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Core Application Routes
api_router.include_router(process.router, prefix="/process", tags=["process"])
api_router.include_router(retrieve.router, prefix="/retrieve", tags=["retrieve"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# Man-O-Man API endpoints (override individual router tags with unified manoman tags)
api_router.include_router(upload.router, prefix="/manoman", tags=["manoman"])
api_router.include_router(classification.router, prefix="/manoman", tags=["manoman"])
api_router.include_router(definition.router, prefix="/manoman", tags=["manoman"])
api_router.include_router(status.router, prefix="/manoman", tags=["manoman"])
api_router.include_router(validation.router, prefix="/manoman", tags=["manoman"])
api_router.include_router(services.router, prefix="/manoman", tags=["manoman"])