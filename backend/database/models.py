from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class DetectionSession(Base):
    __tablename__ = "detection_sessions"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False)  # webcam, video_upload, rtsp
    source_path = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=utc_now)
    ended_at = Column(DateTime, nullable=True)
    total_frames = Column(Integer, default=0)
    status = Column(String(50), default="active")  # active, completed, stopped, error

    detections = relationship("DetectionRecord", back_populates="session", cascade="all, delete-orphan")
    alerts = relationship("AlertLog", back_populates="session", cascade="all, delete-orphan")
    entities = relationship("TrackedEntity", back_populates="session", cascade="all, delete-orphan")


class TrackedEntity(Base):
    __tablename__ = "tracked_entities"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("detection_sessions.id"), index=True)
    tracker_id = Column(Integer, index=True)
    entity_type = Column(String(50), default="human")
    first_seen = Column(DateTime, default=utc_now)
    last_seen = Column(DateTime, default=utc_now)
    max_confidence = Column(Float, default=0.0)
    is_armed_flag = Column(Boolean, default=False)
    total_frames_tracked = Column(Integer, default=0)

    session = relationship("DetectionSession", back_populates="entities")


class DetectionRecord(Base):
    __tablename__ = "detection_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("detection_sessions.id"), index=True)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=utc_now)
    entity_type = Column(String(50), nullable=False)  # human, weapon
    class_name = Column(String(50), nullable=False)   # Person, Handgun, Rifle, Knife, etc.
    confidence = Column(Float, nullable=False)
    
    # Bounding box coordinates normalized (0.0 to 1.0)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)

    tracker_id = Column(Integer, nullable=True, index=True)
    association_status = Column(String(50), nullable=True)  # NONE, UNCERTAIN, PROBABLE, CONFIRMED
    associated_weapon = Column(String(50), nullable=True)

    session = relationship("DetectionSession", back_populates="detections")


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("detection_sessions.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # HUMAN_DETECTED, WEAPON_DETECTED, ASSOCIATION_PROBABLE, UNCERTAIN_ASSOCIATION, TRACKING_LOST, UNUSUAL_MOVEMENT
    severity = Column(String(20), default="INFO")    # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utc_now)
    tracker_id = Column(Integer, nullable=True)
    snapshot_path = Column(String(255), nullable=True)
    acknowledged = Column(Boolean, default=False)

    session = relationship("DetectionSession", back_populates="alerts")
