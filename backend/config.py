import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

# Base directory is the project root (one level above backend)
BASE_DIR = Path(__file__).resolve().parent.parent

class AppConfig(BaseModel):
    base_dir: Path = BASE_DIR

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Database
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"

    # Storage Paths
    data_dir: Path = BASE_DIR / "data"
    uploads_dir: Path = BASE_DIR / "data" / "uploads"
    videos_dir: Path = BASE_DIR / "data" / "videos"
    detections_dir: Path = BASE_DIR / "data" / "detections"
    exports_dir: Path = BASE_DIR / "data" / "exports"

    # Model Weights Paths
    models_dir: Path = BASE_DIR / "models"
    human_model_path: Path = BASE_DIR / "models" / "human" / "yolo11n.pt"
    weapon_model_path: Path = BASE_DIR / "models" / "weapon" / "best.pt"
    pose_model_path: Path = BASE_DIR / "models" / "pose" / "yolo11n-pose.pt"

    # Datasets Path
    datasets_dir: Path = BASE_DIR / "training" / "datasets"

    # Confidence Thresholds
    human_conf_threshold: float = 0.35
    weapon_conf_threshold: float = 0.25
    pose_conf_threshold: float = 0.35
    association_distance_threshold: float = 120.0
    association_iou_threshold: float = 0.15

    # Hardware Device Detection
    device: str = "auto"

    # Video Pipeline Config
    target_fps: int = 25
    frame_width: int = 640
    frame_height: int = 480
    jpeg_quality: int = 80

    def get_device(self) -> str:
        if self.device != "auto":
            return self.device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def ensure_directories(self):
        """Create all required runtime directories if they don't exist."""
        for d in [
            self.data_dir,
            self.uploads_dir,
            self.videos_dir,
            self.detections_dir,
            self.exports_dir,
            self.models_dir / "human",
            self.models_dir / "weapon",
            self.models_dir / "pose",
            self.datasets_dir / "weapons",
        ]:
            d.mkdir(parents=True, exist_ok=True)

config = AppConfig()
config.ensure_directories()
