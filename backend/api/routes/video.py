import shutil
import time
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.config import config
from backend.services.video_processing import video_pipeline

router = APIRouter(prefix="/api/video", tags=["Video Processing"])

class WebcamStartRequest(BaseModel):
    camera_index: int = 0

class RtspStartRequest(BaseModel):
    rtsp_url: str

class VideoFileStartRequest(BaseModel):
    filename: str

def frame_generator():
    """Generates MJPEG multipart stream from pipeline's latest annotated frame."""
    while True:
        frame_bytes = video_pipeline.get_latest_jpeg()
        if frame_bytes is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        time.sleep(0.04)  # ~25 FPS

@router.get("/feed")
def video_feed():
    """MJPEG stream endpoint for real-time video playback in browser <img> tags."""
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/status")
def get_video_status():
    """Returns current status of the video processing pipeline."""
    return video_pipeline.get_status()

@router.post("/start_webcam")
def start_webcam(req: WebcamStartRequest):
    """Starts ingestion and processing from local webcam."""
    try:
        res = video_pipeline.start_webcam(camera_index=req.camera_index)
        return {"success": True, "details": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Uploads an MP4, AVI, or MOV video file to data/uploads."""
    allowed_extensions = [".mp4", ".avi", ".mov", ".mkv"]
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported format {ext}. Allowed: {allowed_extensions}")

    target_path = config.uploads_dir / file.filename
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "success": True,
            "filename": file.filename,
            "size": target_path.stat().st_size,
            "path": str(target_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

@router.post("/start_file")
def start_video_file(req: VideoFileStartRequest):
    """Starts video processing from an uploaded file."""
    target_path = config.uploads_dir / req.filename
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file does not exist")
    try:
        res = video_pipeline.start_video_file(str(target_path))
        return {"success": True, "details": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start_rtsp")
def start_rtsp(req: RtspStartRequest):
    """Connects to and processes an RTSP IP camera stream."""
    try:
        res = video_pipeline.start_rtsp(req.rtsp_url)
        return {"success": True, "details": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pause")
def pause_video():
    video_pipeline.pause()
    return {"success": True, "status": "paused"}

@router.post("/resume")
def resume_video():
    video_pipeline.resume()
    return {"success": True, "status": "resumed"}

@router.post("/stop")
def stop_video():
    video_pipeline.stop()
    return {"success": True, "status": "stopped"}

@router.get("/uploads")
def list_uploaded_videos():
    """Lists all available uploaded videos."""
    videos = []
    if config.uploads_dir.exists():
        for f in config.uploads_dir.iterdir():
            if f.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv"]:
                videos.append({
                    "name": f.name,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "created_at": time.ctime(f.stat().st_ctime)
                })
    return {"videos": videos}
