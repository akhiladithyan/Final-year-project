import cv2
import numpy as np
from typing import Tuple, List, Dict, Any, Optional

def compute_iou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    """
    Computes Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2].
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union_area = box1_area + box2_area - intersection_area
    if union_area <= 0:
        return 0.0
    return float(intersection_area / union_area)

def compute_containment(inner_box: Tuple[float, float, float, float], outer_box: Tuple[float, float, float, float]) -> float:
    """
    Computes the fraction of inner_box contained within outer_box.
    Returns value between 0.0 and 1.0.
    """
    x1 = max(inner_box[0], outer_box[0])
    y1 = max(inner_box[1], outer_box[1])
    x2 = min(inner_box[2], outer_box[2])
    y2 = min(inner_box[3], outer_box[3])

    intersection_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    inner_area = (inner_box[2] - inner_box[0]) * (inner_box[3] - inner_box[1])

    if inner_area <= 0:
        return 0.0
    return float(intersection_area / inner_area)

def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculates Euclidean distance between two 2D points."""
    return float(np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2))

def box_center(box: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """Returns (cx, cy) center of a bounding box [x1, y1, x2, y2]."""
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)

def normalize_bbox(box: Tuple[int, int, int, int], width: int, height: int) -> Tuple[float, float, float, float]:
    """Normalizes pixel coordinates [x1, y1, x2, y2] to range [0, 1]."""
    if width <= 0 or height <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        box[0] / width,
        box[1] / height,
        box[2] / width,
        box[3] / height
    )

def denormalize_bbox(box: Tuple[float, float, float, float], width: int, height: int) -> Tuple[int, int, int, int]:
    """Denormalizes [0, 1] relative coordinates to pixel coordinates."""
    return (
        int(box[0] * width),
        int(box[1] * height),
        int(box[2] * width),
        int(box[3] * height)
    )
