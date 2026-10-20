import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from backend.services.model_manager import model_manager
from backend.tracking.tracker import MultiPersonTracker, TrackRecord
from backend.services.alert_service import alert_service
from backend.utils.preprocessing import compute_iou, box_center, euclidean_distance

logger = logging.getLogger("human_detection")

class HumanDetectionService:
    """
    Module 1: Human Detection and Tracking
    - Detects humans using YOLO11 (COCO class 0: person)
    - Associates detections with persistent tracking IDs using ByteTrack
    - Assigns stable, new unique tracking IDs for each distinct person
    - Updates multi-person tracking history
    """
    def __init__(self):
        self.tracker = MultiPersonTracker()
        self.next_fallback_id = 1

    def process_frame(
        self,
        frame: np.ndarray,
        session_id: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], List[int], List[int]]:
        """
        Processes a single frame for humans and multi-person tracking.
        Returns:
            (human_detections, newly_detected_ids, newly_lost_ids)
        """
        detections: List[Dict[str, Any]] = []
        visible_ids: List[int] = []
        newly_detected_ids: List[int] = []

        if model_manager.human_model is None:
            return detections, newly_detected_ids, []

        try:
            # Run Ultralytics YOLO with ByteTrack persistence
            # class 0 is 'person' in COCO dataset
            results = model_manager.human_model.track(
                source=frame,
                persist=True,
                classes=[0],
                conf=model_manager.human_conf_threshold,
                tracker="bytetrack.yaml",
                verbose=False
            )

            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for box in boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, xyxy)
                    conf = float(box.conf[0].cpu().numpy())
                    curr_box = (float(x1), float(y1), float(x2), float(y2))
                    curr_center = box_center(curr_box)
                    
                    # Extract tracking ID (assigned by ByteTrack)
                    track_id = None
                    if box.id is not None:
                        track_id = int(box.id[0].cpu().numpy())
                    else:
                        # Find spatial match among active tracks not yet seen in this frame
                        best_matched_id = None
                        best_iou = 0.0

                        for tid, existing_track in self.tracker.tracks.items():
                            if tid in visible_ids:
                                continue  # Already claimed by another box in this frame
                            iou = compute_iou(curr_box, tuple(map(float, existing_track.bbox)))
                            if iou > best_iou:
                                best_iou = iou
                                best_matched_id = tid

                        if best_matched_id is not None and best_iou > 0.30:
                            track_id = best_matched_id
                        else:
                            # Check center proximity fallback
                            min_dist = float("inf")
                            for tid, existing_track in self.tracker.tracks.items():
                                if tid in visible_ids:
                                    continue
                                ex_center = box_center(tuple(map(float, existing_track.bbox)))
                                dist = euclidean_distance(curr_center, ex_center)
                                if dist < 80.0 and dist < min_dist:
                                    min_dist = dist
                                    best_matched_id = tid

                            if best_matched_id is not None and min_dist < 80.0:
                                track_id = best_matched_id
                            else:
                                # Genuinely new person entering frame: assign new unique ID
                                max_existing = max(self.tracker.tracks.keys()) if self.tracker.tracks else 0
                                self.next_fallback_id = max(self.next_fallback_id, max_existing) + 1
                                track_id = self.next_fallback_id

                    visible_ids.append(track_id)
                    track_record, is_new = self.tracker.update_or_create(
                        tracker_id=track_id,
                        bbox=(x1, y1, x2, y2),
                        conf=conf
                    )

                    if is_new:
                        newly_detected_ids.append(track_id)

                    detections.append({
                        "tracker_id": track_id,
                        "class_name": "Human",
                        "confidence": round(conf, 4),
                        "bbox": [x1, y1, x2, y2],
                        "frames_tracked": track_record.frames_tracked,
                        "velocity": track_record.current_velocity,
                        "association_status": track_record.association_status,
                        "associated_weapon": track_record.associated_weapon,
                        "is_armed": track_record.is_armed,
                        "armed_weapon_name": track_record.armed_weapon_name
                    })

        except Exception as e:
            logger.error(f"Error in human detection/tracking: {e}")

        # Check for lost tracks
        newly_lost_ids = self.tracker.step_lost_check(visible_ids)

        return detections, newly_detected_ids, newly_lost_ids

    def reset(self):
        self.tracker.reset()
        self.next_fallback_id = 100

human_detection_service = HumanDetectionService()
