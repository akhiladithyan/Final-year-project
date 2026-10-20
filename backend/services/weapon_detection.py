import logging
from typing import List, Dict, Any, Tuple
import numpy as np

from backend.services.model_manager import model_manager
from backend.utils.preprocessing import compute_iou

logger = logging.getLogger("weapon_detection")

# Clean translation map for dataset labels
LABEL_MAPPING = {
    "pisau": "Knife",
    "pistol": "Handgun",
    "senapan": "Rifle",
    "golok": "Machete",
    "pedang": "Sword",
    "kapak": "Axe",
    "celurit": "Sickle",
    "knife": "Knife",
    "handgun": "Handgun",
    "rifle": "Rifle",
    "shotgun": "Shotgun"
}

class WeaponDetectionService:
    """
    Module 2: Weapon Detection
    - Detects visible weapons using custom-trained YOLO model (Handgun, Rifle, Shotgun, Knife)
    - Incorporates COCO Class 43 (Knife) detection to reliably recognize real-world kitchen knives,
      combat knives, and blades out of the box.
    - Resolves and suppresses duplicate bounding boxes via IoU.
    """
    def __init__(self):
        pass

    def is_ready(self) -> bool:
        return (
            (model_manager.weapon_model is not None and model_manager.weapon_model_status == "loaded")
            or model_manager.human_model is not None
        )

    def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs object detection on the frame for weapons (custom weights + COCO knife detector).
        """
        raw_detections: List[Dict[str, Any]] = []

        # 1. Custom Weapon Detector (if loaded)
        if model_manager.weapon_model is not None and model_manager.weapon_model_status == "loaded":
            try:
                # Use a sensitive threshold so kitchen knives and newly trained weapons are caught
                custom_conf = min(0.20, model_manager.weapon_conf_threshold)
                results = model_manager.weapon_model.predict(
                    source=frame,
                    conf=custom_conf,
                    verbose=False
                )
                if results and len(results) > 0 and results[0].boxes is not None:
                    boxes = results[0].boxes
                    names = results[0].names or {}
                    for box in boxes:
                        xyxy = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = map(int, xyxy)
                        conf = float(box.conf[0].cpu().numpy())
                        cls_idx = int(box.cls[0].cpu().numpy())
                        raw_name = names.get(cls_idx, model_manager.weapon_classes[cls_idx % len(model_manager.weapon_classes)])
                        normalized_name = LABEL_MAPPING.get(raw_name.lower(), raw_name)

                        raw_detections.append({
                            "class_name": normalized_name,
                            "confidence": round(conf, 4),
                            "bbox": [x1, y1, x2, y2]
                        })
            except Exception as e:
                logger.error(f"Error in custom weapon model predict: {e}")

        # 2. General Knife & Blade Detector (COCO Class 43: knife, Class 76: scissors)
        # Guarantees kitchen knives, chef knives, paring knives, and utility blades are detected reliably
        if model_manager.human_model is not None:
            try:
                # Class 43 is 'knife', Class 76 is 'scissors' in COCO dataset
                knife_conf = min(0.18, model_manager.weapon_conf_threshold)
                coco_knife_results = model_manager.human_model.predict(
                    source=frame,
                    classes=[43, 76],
                    conf=knife_conf,
                    verbose=False
                )
                if coco_knife_results and len(coco_knife_results) > 0 and coco_knife_results[0].boxes is not None:
                    for box in coco_knife_results[0].boxes:
                        xyxy = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = map(int, xyxy)
                        conf = float(box.conf[0].cpu().numpy())
                        cls_idx = int(box.cls[0].cpu().numpy())
                        item_label = "Knife" if cls_idx == 43 else "Scissors/Blade"

                        raw_detections.append({
                            "class_name": item_label,
                            "confidence": round(conf, 4),
                            "bbox": [x1, y1, x2, y2]
                        })
            except Exception as e:
                logger.error(f"Error in COCO knife detection: {e}")

        # 3. Deduplicate overlapping detections via Non-Maximum Suppression (IoU > 0.45)
        filtered_detections: List[Dict[str, Any]] = []
        # Sort by confidence descending
        raw_detections.sort(key=lambda d: d["confidence"], reverse=True)

        for det in raw_detections:
            overlaps = False
            for existing in filtered_detections:
                iou = compute_iou(tuple(det["bbox"]), tuple(existing["bbox"]))
                if iou > 0.45:
                    overlaps = True
                    break
            if not overlaps:
                filtered_detections.append(det)

        return filtered_detections

weapon_detection_service = WeaponDetectionService()
