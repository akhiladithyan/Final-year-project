import cv2
import time
import asyncio
import logging
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Generator
import numpy as np

from backend.config import config
from backend.services.model_manager import model_manager
from backend.services.human_detection import human_detection_service
from backend.services.weapon_detection import weapon_detection_service
from backend.services.person_association import person_association_service
from backend.services.pose_tracking import pose_tracking_service
from backend.services.movement_analysis import movement_analysis_service
from backend.services.alert_service import alert_service
from backend.tracking.tracker import MultiPersonTracker
from backend.websocket.manager import ws_manager
from backend.database.database import SessionLocal
from backend.database.models import DetectionSession, DetectionRecord
from backend.utils.visualization import (
    draw_hud_header,
    draw_human_box,
    draw_weapon_box,
    draw_pose_skeleton,
    draw_armed_arm_skeleton,
    draw_trajectory,
    get_color_for_id
)

logger = logging.getLogger("video_processing")

class VideoProcessingPipeline:
    """
    Central Video Processing Pipeline coordinating:
    - Frame Acquisition (Webcam, Upload, RTSP)
    - Human Detection & Tracking (Module 1)
    - Weapon Detection (Module 2)
    - Person-Weapon Association (Module 3)
    - Pose & Wrist Tracking (Module 4)
    - Movement Analysis & HUD Visualization (Module 5)
    - Alert Triggering & Telemetry Broadcasting
    """
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.source_type: Optional[str] = None  # "webcam", "upload", "rtsp"
        self.source_target: Optional[str] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        # Frame buffers
        self.latest_raw_frame: Optional[np.ndarray] = None
        self.latest_annotated_frame: Optional[np.ndarray] = None
        self.latest_telemetry: Dict[str, Any] = {}

        # Performance & Stats
        self.fps = 0.0
        self.frame_count = 0
        self.total_humans_detected = 0
        self.session_id: Optional[int] = None
        self.active_loop: Optional[asyncio.AbstractEventLoop] = None

    def start_webcam(self, camera_index: int = 0) -> Dict[str, Any]:
        """Starts video processing from local webcam."""
        self.stop()
        self.source_type = "webcam"
        self.source_target = str(camera_index)
        self._start_session("webcam", f"Camera {camera_index}")
        self._start_worker(camera_index)
        return {"status": "started", "source": f"webcam_{camera_index}"}

    def start_video_file(self, file_path: str) -> Dict[str, Any]:
        """Starts processing an uploaded video file."""
        self.stop()
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Video file not found at {file_path}")
        self.source_type = "upload"
        self.source_target = str(p)
        self._start_session("video_upload", p.name)
        self._start_worker(str(p))
        return {"status": "started", "source": p.name}

    def start_rtsp(self, rtsp_url: str) -> Dict[str, Any]:
        """Starts processing an RTSP IP camera stream."""
        self.stop()
        self.source_type = "rtsp"
        self.source_target = rtsp_url
        self._start_session("rtsp", rtsp_url)
        self._start_worker(rtsp_url)
        return {"status": "started", "source": rtsp_url}

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        """Stops background video capture and pipeline execution."""
        self.stop_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)

        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.is_running = False
        self.is_paused = False
        self._end_session()
        human_detection_service.reset()
        person_association_service.reset()
        logger.info("Video processing pipeline stopped.")

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            active_tracks = human_detection_service.tracker.get_active_tracks()
            active_humans_count = len(active_tracks)
            weapon_detections = self.latest_telemetry.get("weapons", [])
            associations = self.latest_telemetry.get("associations", [])

            return {
                "is_running": self.is_running,
                "is_paused": self.is_paused,
                "source_type": self.source_type,
                "source_target": self.source_target,
                "fps": round(self.fps, 1),
                "frame_count": self.frame_count,
                "session_id": self.session_id,
                "active_humans": active_humans_count,
                "weapons_flagged": len(weapon_detections),
                "associations_count": len(associations),
                "device": model_manager.device,
                "models": model_manager.get_status()["models"]
            }

    def _start_session(self, source_type: str, source_path: str):
        try:
            db = SessionLocal()
            session = DetectionSession(
                source_type=source_type,
                source_path=source_path,
                started_at=datetime.now(timezone.utc),
                status="active"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            self.session_id = session.id
            db.close()
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            self.session_id = 1

    def _end_session(self):
        if self.session_id:
            try:
                db = SessionLocal()
                session = db.query(DetectionSession).filter(DetectionSession.id == self.session_id).first()
                if session:
                    session.ended_at = datetime.now(timezone.utc)
                    session.total_frames = self.frame_count
                    session.status = "completed"
                    db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Error ending session: {e}")
            self.session_id = None

    def _start_worker(self, source):
        self.stop_event.clear()
        self.is_running = True
        self.is_paused = False
        self.frame_count = 0

        # Try to capture event loop for thread-safe async scheduling
        try:
            self.active_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.active_loop = None

        self.worker_thread = threading.Thread(
            target=self._run_pipeline,
            args=(source,),
            daemon=True
        )
        self.worker_thread.start()

    def _run_pipeline(self, source):
        logger.info(f"Video worker thread started for source: {source}")
        self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            logger.error(f"Could not open video source: {source}")
            self.is_running = False
            return

        prev_time = time.time()
        fps_buffer = []

        while not self.stop_event.is_set():
            if self.is_paused:
                time.sleep(0.05)
                continue

            ret, frame = self.cap.read()
            if not ret:
                # If uploaded video reached EOF, loop or stop
                if self.source_type == "upload":
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    logger.warning("Frame read failed or stream closed.")
                    break

            self.frame_count += 1
            start_frame_time = time.time()

            # Execute AI Pipeline on current frame
            annotated_frame, telemetry = self._process_frame_sync(frame)

            # Calculate FPS
            elapsed = time.time() - start_frame_time
            if elapsed > 0:
                cur_fps = 1.0 / elapsed
                fps_buffer.append(cur_fps)
                if len(fps_buffer) > 15:
                    fps_buffer.pop(0)
                self.fps = sum(fps_buffer) / len(fps_buffer)

            with self.lock:
                self.latest_raw_frame = frame
                self.latest_annotated_frame = annotated_frame
                self.latest_telemetry = telemetry

            # Broadcast telemetry to connected WebSockets
            if self.active_loop and self.active_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast_telemetry(telemetry),
                    self.active_loop
                )

            # Cap frame rate if needed
            sleep_time = (1.0 / config.target_fps) - (time.time() - start_frame_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_running = False
        logger.info("Video worker thread finished.")

    def _process_frame_sync(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Executes all 5 modules synchronously on a single frame."""
        h, w = frame.shape[:2]
        annotated = frame.copy()

        # 1. Human Detection and Tracking (Module 1)
        humans, newly_detected_ids, newly_lost_ids = human_detection_service.process_frame(
            frame, session_id=self.session_id
        )

        # 2. Weapon Detection (Module 2)
        weapons = weapon_detection_service.process_frame(frame)

        # 3. Pose Estimation (Module 4)
        poses = pose_tracking_service.process_frame(frame, human_detection_service.tracker)

        # 4. Person-Weapon Association (Module 3)
        associations = person_association_service.associate(
            humans=humans,
            weapons=weapons,
            tracker=human_detection_service.tracker
        )

        # 5. Movement Analysis (Module 5)
        movements, significant_ids = movement_analysis_service.analyze_movement(
            human_detection_service.tracker
        )

        # Trigger Alerts if loop is available
        if self.active_loop and self.active_loop.is_running():
            # Alert for newly detected humans
            for hid in newly_detected_ids:
                asyncio.run_coroutine_threadsafe(
                    alert_service.trigger_alert(
                        alert_type="HUMAN_DETECTED",
                        message=f"Human detected and assigned Tracking ID #{hid:03d}",
                        severity="INFO",
                        tracker_id=hid,
                        session_id=self.session_id
                    ),
                    self.active_loop
                )

            # Alert for weapon detections
            for w_item in weapons:
                asyncio.run_coroutine_threadsafe(
                    alert_service.trigger_alert(
                        alert_type="WEAPON_DETECTED",
                        message=f"Visual weapon sighting ({w_item['class_name']}) requiring human review",
                        severity="WARNING",
                        session_id=self.session_id,
                        frame=frame
                    ),
                    self.active_loop
                )

            # Alert for associations
            for assoc in associations:
                status = assoc["association_status"]
                w_class = assoc["weapon_class"]
                tid = assoc["tracker_id"]
                sev = "CRITICAL" if status == "PROBABLE" else "WARNING"
                asyncio.run_coroutine_threadsafe(
                    alert_service.trigger_alert(
                        alert_type=f"ASSOCIATION_{status}",
                        message=f"{status.capitalize()} association of {w_class} with Person #{tid:03d} (Review Required)",
                        severity=sev,
                        tracker_id=tid,
                        session_id=self.session_id,
                        frame=frame
                    ),
                    self.active_loop
                )

            # Alert for significant body movement
            for sid in significant_ids:
                asyncio.run_coroutine_threadsafe(
                    alert_service.trigger_alert(
                        alert_type="UNUSUAL_MOVEMENT",
                        message=f"Significant velocity change observed for Person #{sid:03d}",
                        severity="INFO",
                        tracker_id=sid,
                        session_id=self.session_id
                    ),
                    self.active_loop
                )

            # Alert for lost tracking
            for lid in newly_lost_ids:
                asyncio.run_coroutine_threadsafe(
                    alert_service.trigger_alert(
                        alert_type="TRACKING_LOST",
                        message=f"Tracking lost for Person #{lid:03d}",
                        severity="INFO",
                        tracker_id=lid,
                        session_id=self.session_id
                    ),
                    self.active_loop
                )

        # Visualizations on annotated frame
        # Draw Trajectories
        for tid, track in human_detection_service.tracker.tracks.items():
            if track.lost_frames == 0:
                color = get_color_for_id(tid)
                draw_trajectory(annotated, track.trajectory, color)

        # Draw Humans (with prominent armed banner if holding weapon)
        for h_item in humans:
            track = human_detection_service.tracker.get_track(h_item["tracker_id"])
            is_armed = track.is_armed if track else h_item.get("is_armed", False)
            assoc_weapon = track.armed_weapon_name if (track and track.armed_weapon_name) else h_item.get("associated_weapon")
            draw_human_box(
                annotated,
                tuple(h_item["bbox"]),
                h_item["tracker_id"],
                h_item["confidence"],
                h_item["association_status"],
                assoc_weapon,
                is_armed=is_armed
            )

        # Draw Weapons
        for w_item in weapons:
            draw_weapon_box(
                annotated,
                tuple(w_item["bbox"]),
                w_item["class_name"],
                w_item["confidence"]
            )

        # Draw Arm Tracking ONLY when an individual is armed
        for tid, pose_data in poses.items():
            track = human_detection_service.tracker.get_track(tid)
            if track and track.is_armed:
                draw_armed_arm_skeleton(
                    annotated,
                    keypoints=pose_data["keypoints"],
                    track_id=tid,
                    wrist_history_left=track.wrist_history_left,
                    wrist_history_right=track.wrist_history_right,
                    weapon_name=track.armed_weapon_name
                )

        # Draw HUD Header
        draw_hud_header(
            annotated,
            fps=self.fps,
            active_humans=len(humans),
            weapons_count=len(weapons),
            device=model_manager.device
        )

        # Prepare Telemetry Payload
        active_tracks = [t.to_dict() for t in human_detection_service.tracker.get_active_tracks()]

        telemetry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "frame_number": self.frame_count,
            "fps": round(self.fps, 1),
            "device": model_manager.device,
            "humans": humans,
            "active_tracks": active_tracks,
            "weapons": weapons,
            "associations": associations,
            "poses": poses,
            "movements": movements
        }

        return annotated, telemetry

    def get_latest_jpeg(self) -> Optional[bytes]:
        """Encodes the latest annotated frame into JPEG bytes."""
        with self.lock:
            if self.latest_annotated_frame is None:
                return None
            ret, jpeg = cv2.imencode(".jpg", self.latest_annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), config.jpeg_quality])
            return jpeg.tobytes() if ret else None

video_pipeline = VideoProcessingPipeline()
