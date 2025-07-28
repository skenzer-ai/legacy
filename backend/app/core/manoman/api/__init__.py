"""
Man-O-Man API Endpoints

FastAPI routers for the Man-O-Man service registry management system:
- Upload API: File upload and processing endpoints
- Classification API: Service classification management endpoints
- Definition API: Interactive service definition endpoints  
- Validation API: Testing and validation endpoints
"""

from .upload import router as upload_router

__all__ = [
    "upload_router"
]