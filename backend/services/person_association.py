import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from backend.utils.preprocessing import compute_iou, compute_containment, euclidean_distance, box_center
from backend.tracking.tracker import MultiPersonTracker

logger = logging.getLogger("person_association")

class PersonAssociationService:
    """
    Module 3: Person-Weapon Association
    Associates visible weapon detections with the corresponding human tracking ID
    based on spatial overlap, wrist proximity, and temporal consistency.
    Labels:
    - NONE: No weapon detected near person
    - UNCERTAIN: Spatial proximity exists, but insufficient evidence or ambiguous overlap
    - PROBABLE: Clear containment/wrist proximity and temporal consistency observed
    """
    def __init__(self):
        # Temporal history: tracker_id -> list of association votes (e.g. [True, True, ...])
        self.association_history: Dict[int, List[Dict[str, Any]]] = {}

    def associate(
        self,
        humans: List[Dict[str, Any]],
        weapons: List[Dict[str, Any]],
        tracker: MultiPersonTracker
    ) -> List[Dict[str, Any]]:
        """
        Calculates spatial and temporal associations between detected humans and weapons.
        Returns a list of association reports.
        """
        associations: List[Dict[str, Any]] = []

        if not weapons or not humans:
            # Clear or decay associations for people without weapons nearby
            for h in humans:
                tid = h.get("tracker_id")
                if tid and tid in tracker.tracks:
                    track = tracker.tracks[tid]
                    track.association_status = "NONE"
                    track.associated_weapon = None
            return associations

        # Match each weapon to candidate humans
        for w_idx, weapon in enumerate(weapons):
            w_box = weapon["bbox"]
            w_class = weapon["class_name"]
            w_conf = weapon["confidence"]
            w_center = box_center(w_box)

            best_human = None
            best_score = 0.0
            best_status = "UNCERTAIN"

            for human in humans:
                h_box = human["bbox"]
                tid = human.get("tracker_id")
                if not tid or tid not in tracker.tracks:
                    continue

                track = tracker.tracks[tid]

                # 1. Spatial Containment (weapon inside or overlapping human bbox)
                containment = compute_containment(w_box, h_box)
                iou = compute_iou(w_box, h_box)

                # Distance from weapon center to human bounding box
                hx1, hy1, hx2, hy2 = h_box
                dx = max(0.0, float(hx1 - w_center[0]), float(w_center[0] - hx2))
                dy = max(0.0, float(hy1 - w_center[1]), float(w_center[1] - hy2))
                box_dist = float(np.sqrt(dx * dx + dy * dy))
                box_proximity = max(0.0, (120.0 - box_dist) / 120.0)

                # 2. Distance from weapon to human wrist keypoints (if pose available)
                wrist_proximity_bonus = 0.0
                if track.pose_keypoints:
                    for wrist_name in ["left_wrist", "right_wrist"]:
                        if wrist_name in track.pose_keypoints:
                            wrist_pt = track.pose_keypoints[wrist_name]
                            if wrist_pt.get("conf", 0) > 0.3:
                                dist = euclidean_distance(w_center, (wrist_pt["x"], wrist_pt["y"]))
                                if dist < 120.0:  # within 120 pixels of wrist
                                    wrist_proximity_bonus = max(wrist_proximity_bonus, (120.0 - dist) / 120.0)

                # Composite evidence score
                score = (containment * 0.4) + (box_proximity * 0.3) + (wrist_proximity_bonus * 0.3)

                if score > best_score:
                    best_score = score
                    best_human = track

            # Determine association category
            if best_human is not None and best_score >= 0.25:
                tid = best_human.tracker_id
                if tid not in self.association_history:
                    self.association_history[tid] = []

                self.association_history[tid].append({
                    "weapon": w_class,
                    "score": best_score,
                    "confidence": w_conf
                })
                if len(self.association_history[tid]) > 10:
                    self.association_history[tid].pop(0)

                # Temporal confirmation: require at least 2 occurrences or strong score
                recent_matches = len(self.association_history[tid])
                if recent_matches >= 2 or best_score >= 0.40:
                    status = "PROBABLE"
                else:
                    status = "UNCERTAIN"

                # Mark human as armed and lock armed state with hold frames
                best_human.mark_armed(w_class, w_conf, hold_frames=90)
                best_human.association_status = status
                best_human.associated_weapon = w_class
                best_human.associated_confidence = w_conf

                associations.append({
                    "tracker_id": tid,
                    "human_bbox": list(best_human.bbox),
                    "weapon_bbox": w_box,
                    "weapon_class": w_class,
                    "weapon_confidence": w_conf,
                    "association_status": status,
                    "evidence_score": round(best_score, 3)
                })

        return associations

    def reset(self):
        self.association_history.clear()

person_association_service = PersonAssociationService()
