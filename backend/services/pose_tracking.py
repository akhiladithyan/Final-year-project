import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from backend.services.model_manager import model_manager
from backend.tracking.tracker import MultiPersonTracker
from backend.utils.preprocessing import compute_iou

logger = logging.getLogger("pose_tracking")

# COCO Keypoint mapping for YOLO Pose
COCO_KEYPOINTS = {
    0: "nose",
    5: "left_shoulder",
    6: "right_shoulder",
    7: "left_elbow",
    8: "right_elbow",
    9: "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip"
}

class PoseTrackingService:
    """
    Module 4: Human Pose and Wrist Tracking
    Tracks upper body keypoints (shoulders, elbows, wrists, hips, nose)
    and associates them with persistent human tracking IDs.
    """
    def __init__(self):
        pass

    def is_ready(self) -> bool:
        return model_manager.pose_model is not None and model_manager.pose_model_status == "loaded"

    def process_frame(
        self,
        frame: np.ndarray,
        tracker: MultiPersonTracker
    ) -> Dict[int, Dict[str, Any]]:
        """
        Runs pose estimation and assigns keypoints to active human tracks.
        Returns:
            Dict mapping tracker_id -> {keypoints: {...}, upper_body_summary: {...}}
        """
        tracked_poses: Dict[int, Dict[str, Any]] = {}

        if not self.is_ready():
            return tracked_poses

        try:
            results = model_manager.pose_model.predict(
                source=frame,
                conf=model_manager.pose_conf_threshold,
                verbose=False
            )

            if results and len(results) > 0 and results[0].keypoints is not None:
                kp_data = results[0].keypoints
                boxes = results[0].boxes

                if kp_data.xy is not None and boxes is not None:
                    poses_xy = kp_data.xy.cpu().numpy()  # shape: (N, 17, 2)
                    conf_data = kp_data.conf.cpu().numpy() if kp_data.conf is not None else None
                    det_boxes = boxes.xyxy.cpu().numpy()  # shape: (N, 4)

                    # Match each detected pose box with existing human tracking IDs
                    for i in range(len(poses_xy)):
                        pose_box = det_boxes[i]
                        keypoints_raw = poses_xy[i]
                        confs = conf_data[i] if conf_data is not None else np.ones(len(keypoints_raw))

                        # Find matching tracker_id via IoU
                        best_tid = None
                        best_iou = 0.0

                        for tid, track in tracker.tracks.items():
                            iou = compute_iou(pose_box, track.bbox)
                            if iou > best_iou:
                                best_iou = iou
                                best_tid = tid

                        if best_tid is not None and best_iou > 0.30:
                            extracted_kps: Dict[str, Dict[str, float]] = {}
                            for idx, name in COCO_KEYPOINTS.items():
                                if idx < len(keypoints_raw):
                                    x, y = keypoints_raw[idx]
                                    c = float(confs[idx]) if idx < len(confs) else 1.0
                                    extracted_kps[name] = {
                                        "x": float(x),
                                        "y": float(y),
                                        "conf": round(c, 3)
                                    }

                            # Update tracker's pose and wrist history
                            track = tracker.tracks[best_tid]
                            track.update_pose(extracted_kps)

                            tracked_poses[best_tid] = {
                                "tracker_id": best_tid,
                                "keypoints": extracted_kps,
                                "left_wrist": extracted_kps.get("left_wrist"),
                                "right_wrist": extracted_kps.get("right_wrist"),
                                "left_elbow": extracted_kps.get("left_elbow"),
                                "right_elbow": extracted_kps.get("right_elbow"),
                                "left_shoulder": extracted_kps.get("left_shoulder"),
                                "right_shoulder": extracted_kps.get("right_shoulder"),
                                "wrist_history_left": track.wrist_history_left,
                                "wrist_history_right": track.wrist_history_right
                            }

        except Exception as e:
            logger.error(f"Error in pose tracking: {e}")

        return tracked_poses

pose_tracking_service = PoseTrackingService()
