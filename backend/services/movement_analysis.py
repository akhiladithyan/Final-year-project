import logging
from typing import Dict, Any, List, Optional
import numpy as np

from backend.tracking.tracker import MultiPersonTracker, TrackRecord

logger = logging.getLogger("movement_analysis")

class MovementAnalysisService:
    """
    Module 5: Movement Analysis and Trajectory Analytics
    Computes body displacement, wrist velocity, and sudden acceleration metrics.
    Triggers informational observation alerts without assuming intent.
    """
    def __init__(self, velocity_threshold: float = 35.0):
        self.velocity_threshold = velocity_threshold

    def analyze_movement(
        self,
        tracker: MultiPersonTracker
    ) -> Tuple[Dict[int, Dict[str, Any]], List[int]]:
        """
        Analyzes movement for all active tracks.
        Returns:
            (analytics_by_tracker_id, list_of_ids_with_significant_movement)
        """
        results: Dict[int, Dict[str, Any]] = {}
        significant_movement_ids: List[int] = []

        for tid, track in tracker.tracks.items():
            if track.lost_frames > 0:
                continue

            # Calculate wrist speeds if trajectories exist
            lw_speed = 0.0
            if len(track.wrist_history_left) >= 2:
                p1, p2 = track.wrist_history_left[-2], track.wrist_history_left[-1]
                lw_speed = float(np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2))

            rw_speed = 0.0
            if len(track.wrist_history_right) >= 2:
                p1, p2 = track.wrist_history_right[-2], track.wrist_history_right[-1]
                rw_speed = float(np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2))

            # Max arm activity
            arm_speed = max(lw_speed, rw_speed)

            # Check significant movement
            is_significant = (track.current_velocity > self.velocity_threshold) or (arm_speed > (self.velocity_threshold * 1.5))
            if is_significant:
                significant_movement_ids.append(tid)

            results[tid] = {
                "tracker_id": tid,
                "body_velocity": round(track.current_velocity, 2),
                "left_wrist_speed": round(lw_speed, 2),
                "right_wrist_speed": round(rw_speed, 2),
                "max_velocity": round(track.max_velocity, 2),
                "is_significant_movement": is_significant,
                "trajectory_length": len(track.trajectory)
            }

        return results, significant_movement_ids

movement_analysis_service = MovementAnalysisService()
