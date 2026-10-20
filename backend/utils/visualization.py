import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

# Color palette for distinct tracking IDs
COLOR_PALETTE = [
    (59, 130, 246),   # Blue
    (16, 185, 129),   # Emerald
    (245, 158, 11),   # Amber
    (168, 85, 247),   # Purple
    (236, 72, 153),   # Pink
    (6, 182, 212),    # Cyan
    (132, 204, 22),   # Lime
    (249, 115, 22),   # Orange
]

WEAPON_COLOR = (0, 0, 220)       # Red for weapons
ASSOCIATION_COLOR = (0, 215, 255) # Gold/Amber for associations

# MediaPipe / YOLO Pose skeleton connections (upper body & core)
SKELETON_CONNECTIONS = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("nose", "left_shoulder"),
    ("nose", "right_shoulder"),
]

def get_color_for_id(track_id: Optional[int]) -> Tuple[int, int, int]:
    """Generates a stable, distinguishable BGR color for each tracking ID."""
    if track_id is None:
        return (150, 150, 150)
    idx = abs(int(track_id)) % len(COLOR_PALETTE)
    # Convert RGB to BGR for OpenCV
    r, g, b = COLOR_PALETTE[idx]
    return (b, g, r)

def draw_hud_header(
    frame: np.ndarray,
    fps: float,
    active_humans: int,
    weapons_count: int,
    device: str
) -> np.ndarray:
    """Draws a sleek semi-transparent top status bar."""
    h, w = frame.shape[:2]
    header_h = 36
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, header_h), (15, 23, 42), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Info text
    info_str = f"FPS: {fps:.1f} | Humans: {active_humans} | Weapons Flagged: {weapons_count} | Dev: {device.upper()}"
    cv2.putText(
        frame,
        info_str,
        (12, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (226, 232, 240),
        1,
        cv2.LINE_AA
    )
    return frame

ARM_CONNECTIONS = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
]

def draw_human_box(
    frame: np.ndarray,
    bbox: Tuple[int, int, int, int],
    track_id: Optional[int],
    confidence: float,
    association_status: Optional[str] = None,
    associated_weapon: Optional[str] = None,
    is_armed: bool = False
) -> np.ndarray:
    """Draws bounding box with tracking ID, confidence, and prominent armed state markers."""
    x1, y1, x2, y2 = bbox

    if is_armed:
        # High-visibility Warning Red for Armed Individuals
        color = (0, 0, 235)  # Bright Red
        thickness = 3

        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        # Armed Alert Header Banner
        id_text = f"ID: {track_id:03d}" if track_id is not None else "Human"
        wpn_text = (associated_weapon or "WEAPON").upper()
        label = f"ARMED [{wpn_text}] | {id_text} | {confidence * 100:.1f}%"

        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 2)
        cv2.rectangle(frame, (x1, max(0, y1 - 26)), (x1 + tw + 12, y1), (0, 0, 200), -1)
        cv2.putText(
            frame,
            label,
            (x1 + 6, max(14, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        # Threat Alert Footer Banner
        footer_text = f"[ARMED THREAT - TRACKING ARMS]"
        (fw, fh), _ = cv2.getTextSize(footer_text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        cv2.rectangle(frame, (x1, y2), (x1 + fw + 10, y2 + 22), (0, 0, 180), -1)
        cv2.putText(
            frame,
            footer_text,
            (x1 + 5, y2 + 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

    else:
        # Standard Clean Neutral/ID Color for Unarmed Individuals
        color = get_color_for_id(track_id)
        thickness = 2

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        id_text = f"ID: {track_id:03d}" if track_id is not None else "Human"
        conf_text = f"{confidence * 100:.1f}%"
        label = f"{id_text} | {conf_text}"

        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - 22)), (x1 + tw + 10, y1), color, -1)
        cv2.putText(
            frame,
            label,
            (x1 + 5, max(12, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        # Minor association badge if uncertain
        if association_status and association_status != "NONE":
            badge_color = (0, 140, 255)
            badge_text = f"[{association_status}]"
            (bw, bh), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1)
            cv2.rectangle(frame, (x1, y2), (x1 + bw + 8, y2 + 18), badge_color, -1)
            cv2.putText(
                frame,
                badge_text,
                (x1 + 4, y2 + 13),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.40,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )

    return frame

def draw_weapon_box(
    frame: np.ndarray,
    bbox: Tuple[int, int, int, int],
    class_name: str,
    confidence: float
) -> np.ndarray:
    """Draws bounding box around detected weapon with distinct warning style."""
    x1, y1, x2, y2 = bbox
    color = WEAPON_COLOR

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    label = f"{class_name.upper()}: {confidence * 100:.1f}%"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.rectangle(frame, (x1, max(0, y1 - 20)), (x1 + tw + 8, y1), color, -1)
    cv2.putText(
        frame,
        label,
        (x1 + 4, max(12, y1 - 5)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )
    return frame

def draw_armed_arm_skeleton(
    frame: np.ndarray,
    keypoints: Dict[str, Dict[str, float]],
    track_id: Optional[int],
    wrist_history_left: Optional[List[Tuple[int, int]]] = None,
    wrist_history_right: Optional[List[Tuple[int, int]]] = None,
    weapon_name: Optional[str] = None
) -> np.ndarray:
    """
    Draws arm-only tracking exclusively for armed individuals:
    - Arm skeleton connections (shoulders, elbows, wrists) in high-contrast threat colors
    - Glowing wrist targeting circles indicating weapon manipulation points
    - Historical wrist motion trails
    """
    bone_color = (0, 70, 255)   # Amber-Red for armed arm bones

    # 1. Draw Wrist Motion Trails for armed person
    for trail, tr_color in [
        (wrist_history_left, (0, 165, 255)),   # Orange trail for left wrist
        (wrist_history_right, (0, 100, 255))   # Red-orange trail for right wrist
    ]:
        if trail and len(trail) >= 2:
            for i in range(1, len(trail)):
                thick = max(1, int(np.sqrt(12 / float(len(trail) - i + 1))))
                cv2.line(frame, trail[i - 1], trail[i], tr_color, thick, cv2.LINE_AA)

    # 2. Draw Arm Bones (Shoulders -> Elbows -> Wrists)
    for pt1_name, pt2_name in ARM_CONNECTIONS:
        if pt1_name in keypoints and pt2_name in keypoints:
            p1 = keypoints[pt1_name]
            p2 = keypoints[pt2_name]
            if p1.get("conf", 1.0) > 0.3 and p2.get("conf", 1.0) > 0.3:
                x1, y1 = int(p1["x"]), int(p1["y"])
                x2, y2 = int(p2["x"]), int(p2["y"])
                cv2.line(frame, (x1, y1), (x2, y2), bone_color, 3, cv2.LINE_AA)

    # 3. Draw Joints with specialized Wrist focus
    for name, pt in keypoints.items():
        if pt.get("conf", 1.0) <= 0.3:
            continue
        x, y = int(pt["x"]), int(pt["y"])

        if "wrist" in name:
            # Concentric glowing target ring on wrists
            cv2.circle(frame, (x, y), 8, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.circle(frame, (x, y), 4, (0, 255, 255), -1, cv2.LINE_AA)
            tag = "L-WRIST" if "left" in name else "R-WRIST"
            cv2.putText(frame, tag, (x + 8, y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1, cv2.LINE_AA)
        elif "elbow" in name:
            cv2.circle(frame, (x, y), 5, (0, 200, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, (x, y), 6, (0, 50, 200), 1, cv2.LINE_AA)
        elif "shoulder" in name:
            cv2.circle(frame, (x, y), 4, (255, 255, 255), -1, cv2.LINE_AA)

    return frame

def draw_pose_skeleton(
    frame: np.ndarray,
    keypoints: Dict[str, Dict[str, float]],
    track_id: Optional[int]
) -> np.ndarray:
    """Draws keypoints and connecting bones for a tracked individual."""
    color = get_color_for_id(track_id)
    h, w = frame.shape[:2]

    # Draw bones
    for pt1_name, pt2_name in SKELETON_CONNECTIONS:
        if pt1_name in keypoints and pt2_name in keypoints:
            p1 = keypoints[pt1_name]
            p2 = keypoints[pt2_name]
            if p1.get("conf", 1.0) > 0.4 and p2.get("conf", 1.0) > 0.4:
                x1, y1 = int(p1["x"]), int(p1["y"])
                x2, y2 = int(p2["x"]), int(p2["y"])
                cv2.line(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

    # Draw joints (wrists, elbows, shoulders highlighted)
    for name, pt in keypoints.items():
        if pt.get("conf", 1.0) > 0.4:
            x, y = int(pt["x"]), int(pt["y"])
            radius = 5 if "wrist" in name else 4
            joint_color = (0, 255, 255) if "wrist" in name else (255, 255, 255)
            cv2.circle(frame, (x, y), radius, joint_color, -1)
            cv2.circle(frame, (x, y), radius + 1, color, 1)

    return frame

def draw_trajectory(
    frame: np.ndarray,
    history: List[Tuple[int, int]],
    color: Tuple[int, int, int]
) -> np.ndarray:
    """Draws movement trajectory trail."""
    if len(history) < 2:
        return frame
    for i in range(1, len(history)):
        thickness = int(np.sqrt(16 / float(len(history) - i + 1))) + 1
        cv2.line(frame, history[i - 1], history[i], color, thickness)
    return frame
