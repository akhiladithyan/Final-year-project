from typing import Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config import config
from backend.services.model_manager import model_manager

router = APIRouter(prefix="/api/models", tags=["Model Management"])

class ThresholdUpdateRequest(BaseModel):
    human_conf: Optional[float] = None
    weapon_conf: Optional[float] = None
    pose_conf: Optional[float] = None

class LoadWeaponWeightsRequest(BaseModel):
    weights_path: str

@router.get("/status")
def get_model_status():
    """Returns status, metadata, device info, and thresholds for all models."""
    return model_manager.get_status()

@router.post("/thresholds")
def update_thresholds(req: ThresholdUpdateRequest):
    """Updates confidence thresholds for detection and pose estimation."""
    model_manager.update_thresholds(
        human_conf=req.human_conf,
        weapon_conf=req.weapon_conf,
        pose_conf=req.pose_conf
    )
    return {
        "success": True,
        "updated_thresholds": {
            "human_conf": model_manager.human_conf_threshold,
            "weapon_conf": model_manager.weapon_conf_threshold,
            "pose_conf": model_manager.pose_conf_threshold
        }
    }

@router.post("/load_weapon_weights")
def load_weapon_weights(req: LoadWeaponWeightsRequest):
    """Loads custom trained YOLO weights for the weapon detection module."""
    success = model_manager.load_custom_weapon_weights(req.weights_path)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load weights from '{req.weights_path}'. Ensure the file exists and is a valid YOLO PyTorch weight file."
        )
    return {
        "success": True,
        "message": "Custom weapon detection weights loaded successfully.",
        "status": model_manager.weapon_model_status
    }

@router.get("/available_weights")
def list_available_weights():
    """Lists weights found in the models directory."""
    weights = []
    for d in [config.models_dir / "weapon", config.models_dir / "human", config.models_dir / "pose"]:
        if d.exists():
            for f in d.iterdir():
                if f.suffix in [".pt", ".onnx"]:
                    weights.append({
                        "filename": f.name,
                        "path": str(f),
                        "module": d.name,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2)
                    })
    return {"weights": weights}
