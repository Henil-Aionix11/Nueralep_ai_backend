"""API router.

Routes:
    docs: Swagger and ReDoc documentation interfaces.
    v1: API version 1.
"""

from fastapi.routing import APIRouter

from app.web.api.docs import router as docs_router
from app.web.api.v1.routes import v1_router


api_router = APIRouter()

api_router.include_router(docs_router, prefix="/v1")
api_router.include_router(v1_router, prefix="/v1")
