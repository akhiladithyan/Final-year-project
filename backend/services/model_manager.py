import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import torch

from backend.config import config

logger = logging.getLogger("model_manager")

class ModelManager:
    """
    Central manager for AI models:
    - Human Detection Model (YOLO11 COCO)
    - Weapon Detection Model (Custom YOLO / Trained weights)
    - Pose Estimation Model (YOLO11-pose or MediaPipe)
    """
    def __init__(self):
        self.device = config.get_device()
        self.human_model = None
        self.weapon_model = None
        self.pose_model = None

        self.human_conf_threshold = config.human_conf_threshold
        self.weapon_conf_threshold = config.weapon_conf_threshold
        self.pose_conf_threshold = config.pose_conf_threshold

        self.human_model_status = "unloaded"
        self.weapon_model_status = "awaiting_training"
        self.pose_model_status = "unloaded"

        self.weapon_classes = ["Handgun", "Rifle", "Shotgun", "Knife"]

        # Attempt eager load of standard models
        self.init_models()

    def init_models(self):
        """Initializes available models with error handling and fallback."""
        self.device = config.get_device()
        logger.info(f"Initializing models on device: {self.device}")

        # 1. Load Human Detection Model (Ultralytics YOLO)
        try:
            from ultralytics import YOLO
            # If local weight does not exist, YOLO will download yolo11n.pt automatically
            human_weight = str(config.human_model_path)
            if not Path(human_weight).exists():
                human_weight = "yolo11n.pt"
            
            logger.info(f"Loading Human detection model: {human_weight}")
            self.human_model = YOLO(human_weight)
            self.human_model.to(self.device)
            self.human_model_status = "loaded"
            logger.info("Human detection model successfully loaded.")
        except Exception as e:
            logger.error(f"Failed to load human detection model: {e}")
            self.human_model_status = f"error: {str(e)}"

        # 2. Check Custom Weapon Detection Model
        weapon_weight = Path(config.weapon_model_path)
        if weapon_weight.exists() and weapon_weight.is_file():
            try:
                self.weapon_model = YOLO(str(weapon_weight))
                self.weapon_model.to(self.device)
                self.weapon_model_status = "loaded"
                if hasattr(self.weapon_model, "names") and self.weapon_model.names:
                    self.weapon_classes = list(self.weapon_model.names.values())
                logger.info(f"Custom Weapon model loaded with classes: {self.weapon_classes}")
            except Exception as e:
                logger.error(f"Failed to load weapon model: {e}")
                self.weapon_model_status = f"error: {str(e)}"
        else:
            logger.info("Weapon model weights not found. Module status: Awaiting Training.")
            self.weapon_model = None
            self.weapon_model_status = "awaiting_training"

        # 3. Load Pose Estimation Model
        try:
            from ultralytics import YOLO
            pose_weight = str(config.pose_model_path)
            if not Path(pose_weight).exists():
                pose_weight = "yolo11n-pose.pt"
            
            logger.info(f"Loading Pose model: {pose_weight}")
            self.pose_model = YOLO(pose_weight)
            self.pose_model.to(self.device)
            self.pose_model_status = "loaded"
            logger.info("Pose estimation model successfully loaded.")
        except Exception as e:
            logger.error(f"Failed to load pose model: {e}")
            self.pose_model_status = f"error: {str(e)}"

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive diagnostic metadata about loaded models."""
        gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None"
        vram_allocated_mb = round(torch.cuda.memory_allocated(0) / (1024 * 1024), 2) if torch.cuda.is_available() else 0

        return {
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": gpu_name,
            "vram_allocated_mb": vram_allocated_mb,
            "models": {
                "human_detection": {
                    "name": "YOLO11 COCO Person Detector",
                    "status": self.human_model_status,
                    "threshold": self.human_conf_threshold,
                    "target_class": "Person (class 0)"
                },
                "weapon_detection": {
                    "name": "Custom YOLO Weapon Detector",
                    "status": self.weapon_model_status,
                    "threshold": self.weapon_conf_threshold,
                    "classes": self.weapon_classes,
                    "weights_path": str(config.weapon_model_path)
                },
                "pose_estimation": {
                    "name": "YOLO11 Pose Keypoint Estimator",
                    "status": self.pose_model_status,
                    "threshold": self.pose_conf_threshold,
                    "keypoints_tracked": ["shoulders", "elbows", "wrists", "hips", "nose"]
                }
            }
        }

    def update_thresholds(
        self,
        human_conf: Optional[float] = None,
        weapon_conf: Optional[float] = None,
        pose_conf: Optional[float] = None
    ):
        """Dynamically updates confidence thresholds."""
        if human_conf is not None:
            self.human_conf_threshold = max(0.05, min(1.0, human_conf))
        if weapon_conf is not None:
            self.weapon_conf_threshold = max(0.05, min(1.0, weapon_conf))
        if pose_conf is not None:
            self.pose_conf_threshold = max(0.05, min(1.0, pose_conf))

    def load_custom_weapon_weights(self, weights_path: str) -> bool:
        """Loads custom trained weights for weapon detection."""
        p = Path(weights_path)
        if not p.exists():
            return False
        try:
            from ultralytics import YOLO
            self.weapon_model = YOLO(str(p))
            self.weapon_model.to(self.device)
            self.weapon_model_status = "loaded"
            if hasattr(self.weapon_model, "names") and self.weapon_model.names:
                self.weapon_classes = list(self.weapon_model.names.values())
            logger.info(f"Custom weapon weights loaded successfully with classes: {self.weapon_classes}")
            return True
        except Exception as e:
            logger.error(f"Failed to load custom weapon weights: {e}")
            self.weapon_model_status = f"error: {str(e)}"
            return False

model_manager = ModelManager()
