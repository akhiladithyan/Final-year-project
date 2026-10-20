import pytest
from fastapi.testclient import TestClient

from backend.config import config
from backend.main import app
from backend.database.database import init_db, SessionLocal
from backend.database.models import DetectionSession, TrackedEntity, AlertLog
from backend.utils.preprocessing import compute_iou, compute_containment, euclidean_distance, box_center
from backend.services.model_manager import model_manager
from backend.tracking.tracker import MultiPersonTracker

client = TestClient(app)

def test_config_and_dirs():
    """Verify configuration and runtime directory presence."""
    assert config.data_dir.exists()
    assert config.uploads_dir.exists()
    assert config.models_dir.exists()
    assert config.get_device() in ["cuda", "cpu"]

def test_database_initialization():
    """Verify database tables and record creation."""
    init_db()
    db = SessionLocal()
    session = DetectionSession(source_type="test", source_path="test.mp4")
    db.add(session)
    db.commit()
    db.refresh(session)

    assert session.id is not None
    assert session.status == "active"

    # Clean up
    db.delete(session)
    db.commit()
    db.close()

def test_preprocessing_utilities():
    """Test geometric calculations."""
    box_a = (0.0, 0.0, 10.0, 10.0)
    box_b = (5.0, 0.0, 15.0, 10.0)
    
    # 5x10 intersection = 50, union = 100 + 100 - 50 = 150 -> IoU = 1/3
    iou = compute_iou(box_a, box_b)
    assert abs(iou - (1.0 / 3.0)) < 1e-4

    # Containment
    inner = (2.0, 2.0, 4.0, 4.0)
    outer = (0.0, 0.0, 10.0, 10.0)
    assert compute_containment(inner, outer) == 1.0

    # Euclidean distance
    assert euclidean_distance((0, 0), (3, 4)) == 5.0
    assert box_center((0, 0, 10, 20)) == (5.0, 10.0)

def test_multi_person_tracker():
    """Test tracker identity persistence and velocity tracking."""
    tracker = MultiPersonTracker()
    track, is_new = tracker.update_or_create(1, (10, 10, 50, 100), 0.95)
    assert is_new is True
    assert track.tracker_id == 1
    assert track.frames_tracked == 1

    # Update track position
    track2, is_new2 = tracker.update_or_create(1, (15, 10, 55, 100), 0.96)
    assert is_new2 is False
    assert track2.frames_tracked == 2
    assert track2.current_velocity == 5.0

    # Step lost check
    lost = tracker.step_lost_check(visible_ids=[])
    assert 1 in lost

def test_model_manager_status():
    """Verify model manager reports correct status and classes."""
    status = model_manager.get_status()
    assert "device" in status
    assert "models" in status
    assert "human_detection" in status["models"]
    assert "weapon_detection" in status["models"]
    assert "pose_estimation" in status["models"]
    assert status["models"]["weapon_detection"]["status"] in ["awaiting_training", "loaded"]

def test_api_health():
    """Test FastAPI /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_api_models_status():
    """Test /api/models/status endpoint."""
    response = client.get("/api/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data

def test_api_tracking_active():
    """Test /api/tracking/active endpoint."""
    response = client.get("/api/tracking/active")
    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data

def test_api_video_uploads():
    """Test /api/video/uploads endpoint."""
    response = client.get("/api/video/uploads")
    assert response.status_code == 200
    data = response.json()
    assert "videos" in data
    assert any(v["name"] == "sample_surveillance.mp4" for v in data["videos"])

def test_api_dataset_info():
    """Test /api/training/dataset_info endpoint."""
    response = client.get("/api/training/dataset_info")
    assert response.status_code == 200
    data = response.json()
    assert "classes" in data
    assert len(data["classes"]) > 0
    # Checks either default or dataset-defined weapon classes
    assert any(c in data["classes"] for c in ["Handgun", "Pistol", "Knife", "Pisau", "Senapan", "Rifle"])

def test_api_alerts_history():
    """Test /api/history/alerts endpoint."""
    response = client.get("/api/history/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_video_pipeline_start_stop():
    """Test starting and stopping video pipeline with local sample video."""
    from backend.services.video_processing import video_pipeline
    sample_path = config.uploads_dir / "sample_surveillance.mp4"
    if sample_path.exists():
        res = video_pipeline.start_video_file(str(sample_path))
        assert res["status"] == "started"
        assert video_pipeline.is_running is True

        import time
        time.sleep(0.5)

        status = video_pipeline.get_status()
        assert status["is_running"] is True

        video_pipeline.stop()
        assert video_pipeline.is_running is False

