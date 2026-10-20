import sys
from pathlib import Path

# Add project root to sys.path so 'backend' is recognized regardless of working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import config
from backend.database.database import init_db
from backend.websocket.manager import ws_manager
from backend.services.video_processing import video_pipeline

from backend.api.routes.video import router as video_router
from backend.api.routes.detection import router as detection_router
from backend.api.routes.tracking import router as tracking_router
from backend.api.routes.models import router as models_router
from backend.api.routes.training import router as training_router
from backend.api.routes.history import router as history_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure directories and database tables exist
    logger.info("Initializing system database...")
    init_db()
    logger.info("System database initialized.")
    yield
    # Shutdown: Stop any running video processing pipelines
    logger.info("Shutting down video processing pipeline...")
    video_pipeline.stop()
    logger.info("Application shutdown complete.")

app = FastAPI(
    title="AI-Powered Armed Human Detection & Movement Tracking System",
    description="Passive Computer Vision Situational-Awareness System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API Routers
app.include_router(video_router)
app.include_router(detection_router)
app.include_router(tracking_router)
app.include_router(models_router)
app.include_router(training_router)
app.include_router(history_router)

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; clients can send ping or commands if needed
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        ws_manager.disconnect(websocket)

@app.get("/api/health")
def healthcheck():
    return {
        "status": "healthy",
        "device": config.get_device(),
        "video_pipeline_running": video_pipeline.is_running
    }

# Mount Compiled Frontend if present
frontend_dist = config.base_dir / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)
