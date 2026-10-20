import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timezone
import numpy as np

def utc_now():
    return datetime.now(timezone.utc)

class TrackRecord:
    """Maintains state and trajectory history for a single tracked human."""
    def __init__(self, tracker_id: int, initial_bbox: Tuple[int, int, int, int], initial_conf: float):
        self.tracker_id = tracker_id
        self.bbox = initial_bbox
        self.confidence = initial_conf
        self.first_seen = utc_now()
        self.last_seen = utc_now()
        self.frames_tracked = 1
        self.lost_frames = 0
        self.trajectory: List[Tuple[int, int]] = []
        self.pose_keypoints: Dict[str, Dict[str, float]] = {}
        self.wrist_history_left: List[Tuple[int, int]] = []
        self.wrist_history_right: List[Tuple[int, int]] = []
        self.association_status = "NONE"
        self.associated_weapon = None
        self.associated_confidence = 0.0

        # Armed status persistence
        self.is_armed = False
        self.armed_hold_frames = 0
        self.armed_weapon_name = None

        # Movement metrics
        self.current_velocity = 0.0
        self.max_velocity = 0.0

        # Append initial center
        cx = int((initial_bbox[0] + initial_bbox[2]) / 2)
        cy = int((initial_bbox[1] + initial_bbox[3]) / 2)
        self.trajectory.append((cx, cy))

    def update(self, bbox: Tuple[int, int, int, int], conf: float):
        self.bbox = bbox
        self.confidence = conf
        self.last_seen = utc_now()
        self.frames_tracked += 1
        self.lost_frames = 0

        # Decay armed hold frames if not actively reinforced
        if self.armed_hold_frames > 0:
            self.armed_hold_frames -= 1
            self.is_armed = True
        else:
            self.is_armed = False

        cx = int((bbox[0] + bbox[2]) / 2)
        cy = int((bbox[1] + bbox[3]) / 2)

        if self.trajectory:
            prev_cx, prev_cy = self.trajectory[-1]
            dist = np.sqrt((cx - prev_cx) ** 2 + (cy - prev_cy) ** 2)
            self.current_velocity = float(dist)
            self.max_velocity = max(self.max_velocity, self.current_velocity)

        self.trajectory.append((cx, cy))
        if len(self.trajectory) > 60:
            self.trajectory.pop(0)

    def mark_armed(self, weapon_name: str, confidence: float, hold_frames: int = 90):
        """Marks person as actively armed with hold frames for occlusion resistance."""
        self.is_armed = True
        self.armed_weapon_name = weapon_name
        self.associated_weapon = weapon_name
        self.associated_confidence = confidence
        self.armed_hold_frames = hold_frames

    def update_pose(self, keypoints: Dict[str, Dict[str, float]]):
        self.pose_keypoints = keypoints
        if "left_wrist" in keypoints and keypoints["left_wrist"].get("conf", 0) > 0.4:
            lw = (int(keypoints["left_wrist"]["x"]), int(keypoints["left_wrist"]["y"]))
            self.wrist_history_left.append(lw)
            if len(self.wrist_history_left) > 40:
                self.wrist_history_left.pop(0)

        if "right_wrist" in keypoints and keypoints["right_wrist"].get("conf", 0) > 0.4:
            rw = (int(keypoints["right_wrist"]["x"]), int(keypoints["right_wrist"]["y"]))
            self.wrist_history_right.append(rw)
            if len(self.wrist_history_right) > 40:
                self.wrist_history_right.pop(0)

    def mark_lost(self):
        self.lost_frames += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tracker_id": self.tracker_id,
            "bbox": list(self.bbox),
            "confidence": round(self.confidence, 4),
            "frames_tracked": self.frames_tracked,
            "lost_frames": self.lost_frames,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "velocity": round(self.current_velocity, 2),
            "max_velocity": round(self.max_velocity, 2),
            "association_status": self.association_status,
            "associated_weapon": self.associated_weapon,
            "associated_confidence": round(self.associated_confidence, 4),
            "is_armed": self.is_armed,
            "armed_weapon_name": self.armed_weapon_name,
            "pose_available": bool(self.pose_keypoints)
        }


class MultiPersonTracker:
    """Maintains active identity tracks and coordinates tracking across frames."""
    def __init__(self, max_lost_frames: int = 30):
        self.tracks: Dict[int, TrackRecord] = {}
        self.max_lost_frames = max_lost_frames

    def get_track(self, tracker_id: int) -> Optional[TrackRecord]:
        return self.tracks.get(tracker_id)

    def update_or_create(self, tracker_id: int, bbox: Tuple[int, int, int, int], conf: float) -> Tuple[TrackRecord, bool]:
        """Returns (track_record, is_new)."""
        if tracker_id in self.tracks:
            track = self.tracks[tracker_id]
            track.update(bbox, conf)
            return track, False
        else:
            track = TrackRecord(tracker_id, bbox, conf)
            self.tracks[tracker_id] = track
            return track, True

    def step_lost_check(self, visible_ids: List[int]) -> List[int]:
        """Flags lost tracks and returns newly lost IDs."""
        newly_lost = []
        expired_ids = []

        for tid, track in self.tracks.items():
            if tid not in visible_ids:
                track.mark_lost()
                if track.lost_frames == 1:
                    newly_lost.append(tid)
                elif track.lost_frames > self.max_lost_frames:
                    expired_ids.append(tid)

        for tid in expired_ids:
            del self.tracks[tid]

        return newly_lost

    def get_active_tracks(self) -> List[TrackRecord]:
        return [t for t in self.tracks.values() if t.lost_frames == 0]

    def reset(self):
        self.tracks.clear()
