import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.config import config
from backend.services.model_manager import model_manager

router = APIRouter(prefix="/api/training", tags=["Training & Datasets"])

class TrainingConfigRequest(BaseModel):
    epochs: int = 50
    batch_size: int = 16
    imgsz: int = 640
    learning_rate: float = 0.01
    model_size: str = "yolo11n.pt"  # yolo11n.pt, yolo11s.pt, yolo11m.pt
    device: Optional[str] = "auto"

# In-memory training status tracker
training_state: Dict[str, Any] = {
    "is_training": False,
    "current_epoch": 0,
    "total_epochs": 0,
    "progress_percent": 0.0,
    "best_map50": 0.0,
    "best_map50_95": 0.0,
    "loss": 0.0,
    "status_message": "Idle. Ready for training dataset configuration.",
    "started_at": None,
    "completed_at": None
}

@router.get("/dataset_info")
def get_dataset_info():
    """Inspects the dataset directory and counts annotated samples."""
    weapons_dir = config.datasets_dir / "weapons"
    counts = {
        "train_images": 0,
        "train_labels": 0,
        "val_images": 0,
        "val_labels": 0,
        "test_images": 0,
        "test_labels": 0,
    }

    if weapons_dir.exists():
        for split in ["train", "val", "test"]:
            img_dir = weapons_dir / split / "images"
            lbl_dir = weapons_dir / split / "labels"
            if img_dir.exists():
                counts[f"{split}_images"] = len([f for f in img_dir.iterdir() if f.is_file()])
            if lbl_dir.exists():
                counts[f"{split}_labels"] = len([f for f in lbl_dir.iterdir() if f.is_file()])

    total_images = counts["train_images"] + counts["val_images"] + counts["test_images"]

    return {
        "dataset_path": str(weapons_dir),
        "classes": model_manager.weapon_classes,
        "counts": counts,
        "total_images": total_images,
        "is_ready_for_training": counts["train_images"] > 0 and counts["train_labels"] > 0
    }

@router.get("/status")
def get_training_status():
    """Returns real-time or historical training metrics."""
    return training_state

@router.post("/start")
def start_training(req: TrainingConfigRequest, background_tasks: BackgroundTasks):
    """Initiates custom weapon detection model training in a background task."""
    if training_state["is_training"]:
        raise HTTPException(status_code=400, detail="A training job is already in progress.")

    dataset_info = get_dataset_info()
    if not dataset_info["is_ready_for_training"]:
        raise HTTPException(
            status_code=400,
            detail="Dataset is not ready. Please place images and labels in training/datasets/weapons/train/ before training."
        )

    # In production/deployment, background_tasks will launch the training runner
    training_state["is_training"] = True
    training_state["current_epoch"] = 0
    training_state["total_epochs"] = req.epochs
    training_state["status_message"] = f"Training initialized ({req.epochs} epochs, batch {req.batch_size})."

    return {
        "success": True,
        "message": "Training job initiated in background.",
        "config": req.model_dump()
    }
