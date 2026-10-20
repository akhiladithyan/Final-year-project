from fastapi import APIRouter
from backend.services.video_processing import video_pipeline

router = APIRouter(prefix="/api/detection", tags=["Detections"])

@router.get("/current")
def get_current_detections():
    """Returns the latest frame's detection telemetry."""
    return video_pipeline.latest_telemetry
