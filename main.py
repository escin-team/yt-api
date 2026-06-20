"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from youtube_search.config import get_settings
from youtube_search.api.v1 import search, download, playlist, docs
from youtube_search.api.v1.search_prefetch import router as prefetch_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="YouTube Music Streaming API",
    description="Zero-cost YouTube music streaming API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "youtube-search-api",
        "version": "1.0.0",
        "port": settings.api_port,
        "cache": "in-memory" if not settings.redis_enabled else "redis",
        "cloudinary_accounts": len(settings.cloudinary_accounts)
    }

@app.get("/")
async def root():
    return {
        "message": "YouTube Music Streaming API",
        "docs": "/docs",
        "health": "/health"
    }

# ⭐ Register routers - router sudah punya prefix sendiri
app.include_router(search.router)
app.include_router(prefetch_router)  # ⭐ Tambahan untuk search-and-prefetch
app.include_router(download.router)
app.include_router(playlist.router)
app.include_router(docs.router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting YouTube Music API on port {settings.api_port}")
    logger.info(f"Redis enabled: {settings.redis_enabled}")
    logger.info(f"Cloudinary accounts: {len(settings.cloudinary_accounts)}")
    logger.info(f"Download timeout: {settings.download_timeout} seconds")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=False)