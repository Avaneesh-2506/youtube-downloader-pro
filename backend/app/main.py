import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.endpoints import router as api_v1_router
from app.services.ffmpeg_locator import get_ffmpeg_path
from app.services.cleanup_service import start_periodic_cleanup_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    ffmpeg_bin = get_ffmpeg_path()
    if ffmpeg_bin:
        logger.info(f"FFmpeg binary detected and ready: {ffmpeg_bin}")
    else:
        logger.warning("WARNING: FFmpeg not detected! 1080p and high-res video muxing will fail without FFmpeg.")

    # Start garbage collector task
    cleanup_task = asyncio.create_task(start_periodic_cleanup_loop())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(api_v1_router, prefix="/api")

@app.get("/health", tags=["system"])
async def health_check():
    import os
    ffmpeg_bin = get_ffmpeg_path()
    has_cookie = os.path.exists(settings.COOKIE_PATH)
    cookie_size = os.path.getsize(settings.COOKIE_PATH) if has_cookie else 0
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ffmpeg_ready": bool(ffmpeg_bin),
        "ffmpeg_path": ffmpeg_bin,
        "cookies_loaded": has_cookie,
        "cookie_file_size": cookie_size,
    }

@app.get("/", tags=["system"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API. Visit /docs for interactive Swagger documentation."
    }
