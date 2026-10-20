from fastapi import APIRouter, HTTPException
from backend.services.human_detection import human_detection_service

router = APIRouter(prefix="/api/tracking", tags=["Tracking"])

@router.get("/active")
def get_active_tracks():
    """Returns all currently active tracked persons with identities, velocities, and statuses."""
    tracks = human_detection_service.tracker.get_active_tracks()
    return {
        "count": len(tracks),
        "tracks": [t.to_dict() for t in tracks]
    }

@router.get("/{tracker_id}")
def get_track_detail(tracker_id: int):
    """Returns detailed history, trajectories, and pose coordinates for a specific person."""
    track = human_detection_service.tracker.get_track(tracker_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Tracking ID #{tracker_id} not found.")

    return {
        "tracker_id": track.tracker_id,
        "bbox": list(track.bbox),
        "confidence": track.confidence,
        "frames_tracked": track.frames_tracked,
        "first_seen": track.first_seen.isoformat(),
        "last_seen": track.last_seen.isoformat(),
        "current_velocity": track.current_velocity,
        "max_velocity": track.max_velocity,
        "trajectory": track.trajectory,
        "association_status": track.association_status,
        "associated_weapon": track.associated_weapon,
        "pose_keypoints": track.pose_keypoints,
        "wrist_history_left": track.wrist_history_left,
        "wrist_history_right": track.wrist_history_right
    }
