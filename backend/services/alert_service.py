import time
import logging
import cv2
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from backend.config import config
from backend.database.database import SessionLocal
from backend.database.models import AlertLog
from backend.websocket.manager import ws_manager

logger = logging.getLogger("alert_service")

class AlertService:
    """
    Manages informational alerts for human detection, weapon sightings,
    person-weapon associations, and movement observations.
    All alerts require human review.
    """
    def __init__(self):
        self.cooldowns: Dict[str, float] = {}
        self.default_cooldown_sec = 4.0  # seconds between repeated alerts for the same event key

    async def trigger_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "INFO",
        tracker_id: Optional[int] = None,
        session_id: Optional[int] = None,
        frame: Optional[np.ndarray] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Creates, records, and broadcasts an alert event if cooldown has elapsed.
        """
        cooldown_key = f"{alert_type}_{tracker_id or 'global'}"
        now = time.time()

        if cooldown_key in self.cooldowns and (now - self.cooldowns[cooldown_key]) < self.default_cooldown_sec:
            return None  # Suppress repetitive alerts

        self.cooldowns[cooldown_key] = now

        # Save snapshot if frame is provided
        snapshot_filename = None
        if frame is not None:
            ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            snapshot_filename = f"alert_{alert_type}_{ts_str}.jpg"
            snapshot_path = config.detections_dir / snapshot_filename
            try:
                cv2.imwrite(str(snapshot_path), frame)
            except Exception as e:
                logger.error(f"Failed to save alert snapshot: {e}")
                snapshot_filename = None

        alert_dict = {
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tracker_id": tracker_id,
            "session_id": session_id,
            "snapshot_url": f"/api/history/snapshots/{snapshot_filename}" if snapshot_filename else None,
            "acknowledged": False
        }

        # Persist to SQLite
        try:
            db = SessionLocal()
            record = AlertLog(
                session_id=session_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                tracker_id=tracker_id,
                snapshot_path=str(snapshot_filename) if snapshot_filename else None,
                acknowledged=False
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            alert_dict["id"] = record.id
            db.close()
        except Exception as e:
            logger.error(f"Database error while saving alert: {e}")

        # Broadcast via WebSocket
        await ws_manager.broadcast_alert(alert_dict)
        logger.info(f"Alert triggered: [{severity}] {alert_type}: {message}")

        return alert_dict

alert_service = AlertService()
