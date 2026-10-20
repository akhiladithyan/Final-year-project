from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.config import config
from backend.database.database import get_db
from backend.database.models import AlertLog, DetectionSession

router = APIRouter(prefix="/api/history", tags=["History & Alerts"])

@router.get("/alerts")
def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves recorded alert events sorted by newest first."""
    query = db.query(AlertLog)
    if severity:
        query = query.filter(AlertLog.severity == severity.upper())
    alerts = query.order_by(desc(AlertLog.timestamp)).limit(limit).all()

    return [
        {
            "id": a.id,
            "session_id": a.session_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "tracker_id": a.tracker_id,
            "snapshot_url": f"/api/history/snapshots/{Path(a.snapshot_path).name}" if a.snapshot_path else None,
            "acknowledged": a.acknowledged
        }
        for a in alerts
    ]

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Marks an alert as reviewed/acknowledged."""
    alert = db.query(AlertLog).filter(AlertLog.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    return {"success": True, "alert_id": alert_id}

@router.get("/sessions")
def get_sessions(limit: int = 20, db: Session = Depends(get_db)):
    """Retrieves recorded detection sessions."""
    sessions = db.query(DetectionSession).order_by(desc(DetectionSession.started_at)).limit(limit).all()
    return [
        {
            "id": s.id,
            "source_type": s.source_type,
            "source_path": s.source_path,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "total_frames": s.total_frames,
            "status": s.status
        }
        for s in sessions
    ]

@router.get("/snapshots/{filename}")
def get_snapshot(filename: str):
    """Serves detection snapshot images."""
    file_path = config.detections_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Snapshot file not found")
    return FileResponse(str(file_path), media_type="image/jpeg")
