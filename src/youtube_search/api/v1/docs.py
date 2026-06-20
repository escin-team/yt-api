"""Docs endpoint untuk redirect ke Swagger UI."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["Docs"])


@router.get("/docs")
async def docs_redirect():
    """Redirect /api/docs ke /docs (Swagger UI)."""
    return RedirectResponse(url="/docs")