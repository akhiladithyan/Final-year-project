# AI-Powered Armed Human Detection & Movement Tracking System

> **Passive Computer Vision Situational-Awareness & Operator Review Platform**  
> *Built with PyTorch, Ultralytics YOLO11, ByteTrack, OpenCV, FastAPI, and React.*

---

## 1. Executive Summary & Operational Scope

The **AI-Powered Armed Human Detection & Movement Tracking System** is a modular, real-time computer vision system designed for security monitoring, perimeter protection, and situational awareness. 

### Operational Scope & Ethical Guardrails
- **Passive Monitoring Only**: This system strictly monitors video feeds, detects patterns, and provides informational telemetry for human review.
- **No Autonomous Action**: It does **not** control weapons, initiate engagement, predict targets, or automate physical responses.
- **Review Gating**: Detections and associations are explicitly labeled as `HUMAN DETECTED`, `WEAPON DETECTED`, `ASSOCIATION PROBABLE`, or `ASSOCIATION UNCERTAIN`. Detections are never presented as proof of intent or ownership.

---

## 2. Core Architecture: Five Independent AI Modules

The application is structured into five decoupled AI and computer vision modules:

```text
               Video Input (Webcam / Upload / RTSP)
                                |
                                v
                   [Video Processing Pipeline]
                                |
                                v
               [Module 1: Human Detection & Tracking]
                   (YOLO11 COCO + ByteTrack)
                                |
                +---------------+---------------+
                |                               |
                v                               v
    [Module 2: Weapon Detection]   [Module 4: Upper-Body Pose]
     (Custom YOLO: Handgun, Rifle,  (YOLO11 Pose / MediaPipe)
      Shotgun, Knife)                           |
                |                               |
                v                               |
 [Module 3: Person Association]                 |
  (Containment & Wrist Proximity)               |
                |                               |
                +---------------+---------------+
                                |
                                v
            [Module 5: Movement Analytics & HUD Alerting]
             (Velocity Spikes, Trajectory, Cooldowns)
                                |
                                v
               FastAPI Backend (REST & WebSocket)
                                |
                                v
               React Vite Command Center Dashboard
```

### Module 1: Human Detection & Multi-Person Tracking
- Detects humans using Ultralytics YOLO (`person` class 0).
- Employs **ByteTrack** to maintain stable numerical tracking IDs (`#001`, `#002`, etc.) across frames, occlusions, and camera pans.
- Tracks detection confidence and velocity (pixels/frame).

### Module 2: Weapon Detection
- Independent YOLO object detection model trained on weapon classes:
  - `Handgun`
  - `Rifle`
  - `Shotgun`
  - `Knife`
- Supports custom dataset training, validation, and testing workflows.
- Strictly respects confidence thresholds to avoid treating unverified objects as confirmed weapons.
- Reports `Awaiting Training` when weights have not yet been trained or loaded.

### Module 3: Person-Weapon Association
- Assesses spatial containment ($0.0 \text{ to } 1.0$), bounding box IoU, and Euclidean distance to human wrist keypoints.
- Enforces a temporal confirmation window (at least 3 matching frames) before upgrading an association to `ASSOCIATION PROBABLE`.
- Ambiguous overlaps remain flagged as `ASSOCIATION UNCERTAIN`.

### Module 4: Human Pose & Upper-Body Landmark Tracking
- Extracts anatomical keypoints: Left/Right Shoulders, Elbows, Wrists, Hips, and Nose.
- Maps landmarks directly to the human tracking ID.
- Maintains position histories for left and right wrists to analyze arm movements.

### Module 5: Movement Visualization & Informational Alerting
- Calculates body displacement, wrist speeds, and sudden acceleration spikes.
- Visualizes colored bounding boxes, skeletons, and trajectory trails on a high-definition MJPEG HUD overlay.
- Dispatches rate-limited informational alerts:
  - `HUMAN_DETECTED`
  - `WEAPON_DETECTED` (Requires Human Review)
  - `ASSOCIATION_PROBABLE`
  - `ASSOCIATION_UNCERTAIN`
  - `TRACKING_LOST`
  - `UNUSUAL_MOVEMENT`

---

## 3. Technology Stack

- **AI & Vision**: Python 3.11–3.14, PyTorch, Ultralytics YOLO (YOLO11), OpenCV, ByteTrack, NumPy, Pandas, Scipy
- **Backend**: FastAPI, Uvicorn, WebSockets, SQLAlchemy, SQLite (PostgreSQL ready), Pydantic v2
- **Frontend**: React 19, Vite, Tailwind CSS v4, Recharts, Lucide React
- **Hardware Acceleration**: Automatic CUDA detection (tested on NVIDIA GeForce RTX 4050 6GB) with transparent CPU fallback.

---

## 4. Project Directory Structure

```text
Final year project/
├── backend/
│   ├── main.py                  # FastAPI application entrypoint & static mount
│   ├── config.py                # Centralized configuration & directory setup
│   ├── api/routes/
│   │   ├── video.py             # Webcam, Upload, RTSP, MJPEG streaming
│   │   ├── detection.py         # Instant detection telemetry
│   │   ├── tracking.py          # Active tracks & trajectory queries
│   │   ├── models.py            # Model statuses & threshold tuning
│   │   ├── training.py          # Dataset inspection & training lifecycle
│   │   └── history.py           # Persistent alerts & session audits
│   ├── services/
│   │   ├── human_detection.py   # Module 1: YOLO + ByteTrack
│   │   ├── weapon_detection.py  # Module 2: Weapon detector wrapper
│   │   ├── person_association.py# Module 3: Spatial & temporal association
│   │   ├── pose_tracking.py     # Module 4: Upper-body pose estimator
│   │   ├── movement_analysis.py # Module 5: Velocity & trajectory analytics
│   │   ├── video_processing.py  # Unified multi-source pipeline worker
│   │   ├── alert_service.py     # Cooldown-gated informational alerts
│   │   └── model_manager.py     # PyTorch model loader & device manager
│   ├── tracking/
│   │   └── tracker.py           # Multi-person identity tracker
│   ├── database/
│   │   ├── database.py          # SQLAlchemy SQLite engine
│   │   └── models.py            # Sessions, Detections, Alerts tables
│   ├── websocket/
│   │   └── manager.py           # Real-time WebSocket broadcasting
│   └── utils/
│       ├── visualization.py     # OpenCV HUD & skeleton rendering
│       └── preprocessing.py     # IoU, containment, Euclidean distance
├── frontend/
│   ├── src/
│   │   ├── layouts/DashboardLayout.jsx # Command-center layout & top HUD
│   │   ├── pages/
│   │   │   ├── Overview.jsx            # Telemetry cards & quick controls
│   │   │   ├── LiveDetection.jsx       # Live video stream & side panel
│   │   │   ├── HumanTracking.jsx       # Multi-person identity table
│   │   │   ├── WeaponDetection.jsx     # Weapon engine & sensitivity slider
│   │   │   ├── PoseTracking.jsx        # Keypoints & Recharts velocity
│   │   │   ├── DetectionHistory.jsx    # Alert log & snapshot preview
│   │   │   ├── ModelManagement.jsx     # GPU stats & confidence gating
│   │   │   ├── DatasetTraining.jsx     # Training guide & run controls
│   │   │   └── Settings.jsx            # FPS limits & tracker reset
│   │   ├── hooks/useTelemetryWebSocket.js # Reconnecting WebSocket hook
│   │   ├── services/api.js             # REST API client
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── training/
│   ├── datasets/weapons/
│   │   ├── data.yaml            # Dataset YAML definition
│   │   ├── train/ (images, labels)
│   │   ├── val/ (images, labels)
│   │   └── test/ (images, labels)
│   ├── scripts/
│   │   ├── train_weapon.py      # Custom model training script
│   │   ├── validate_weapon.py   # mAP50, mAP50-95, precision, recall
│   │   └── evaluate_model.py    # Latency benchmark & visual evaluation
│   ├── reports/                 # Output confusion matrices and plots
│   └── DATASET_TRAINING_GUIDE.md# Step-by-step dataset walkthrough
├── models/
│   ├── human/                   # Pretrained person weights
│   ├── weapon/                  # Custom trained weapon weights (best.pt)
│   └── pose/                    # Pose estimation weights
├── data/
│   ├── uploads/                 # Uploaded surveillance videos (MP4, AVI)
│   ├── videos/                  # Sample test videos
│   ├── detections/              # Incident snapshot JPEGs
│   └── app.db                   # SQLite database
├── tests/
│   ├── test_backend.py          # Pytest unit & integration test suite
│   └── create_test_video.py     # Synthetic surveillance video generator
├── requirements.txt
├── DEVELOPMENT_STATUS.md
└── .env.example
```

---

## 5. Quickstart & Installation

### Step 1: Clone Repository & Setup Virtual Environment
```bash
# In project root
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 6. Running the Application

### Option A: Single Command Full-Stack Mode (Recommended)
Because the compiled React frontend is mounted directly in FastAPI:
```bash
python backend/main.py
```
Open your browser at: **`http://localhost:8000`**

### Option B: Development Mode (with Hot Module Reloading)
Terminal 1 (Backend API & WebSocket):
```bash
python backend/main.py
```
Terminal 2 (React Vite Dev Server):
```bash
cd frontend
npm run dev
```
Open your browser at: **`http://localhost:5173`**

---

## 7. Video Input Usage

### A. Webcam
1. Navigate to **Overview** or **Live Detection**.
2. Select your camera device index (0 for default built-in camera, 1 or 2 for external USB cameras).
3. Click **Start Camera**.

### B. Video File Upload
1. Under **Overview** &rarr; **Video File Processing**, click **Upload** and select an `.mp4`, `.avi`, or `.mov` file.
2. Select the file from the dropdown and click **Start File**.
3. A sample surveillance video (`sample_surveillance.mp4`) is already included in `data/uploads/`.

### C. RTSP Surveillance Stream
1. Enter the network RTSP URL (e.g. `rtsp://admin:password@192.168.1.100:554/live`).
2. Click **Connect RTSP**.

---

## 8. Custom Weapon Model Training Workflow

See [`training/DATASET_TRAINING_GUIDE.md`](file:///training/DATASET_TRAINING_GUIDE.md) for full instructions.

### 1. Place Annotated Images & Labels
- Training data: `training/datasets/weapons/train/images` and `labels`
- Validation data: `training/datasets/weapons/val/images` and `labels`
- **Negative samples**: Place images with everyday objects (phones, tools) in `train/images` with empty `.txt` files in `train/labels`.

### 2. Launch Training via CLI or UI
```bash
# Uses RTX 4050 GPU (CUDA)
python training/scripts/train_weapon.py --epochs 50 --batch 16 --imgsz 640
```
- Best model weights will be exported to `models/weapon/best.pt`.
- The dashboard automatically detects `models/weapon/best.pt` and activates the Weapon Detector.

### 3. Validate Metrics
```bash
python training/scripts/validate_weapon.py --weights models/weapon/best.pt --split val
```
Generates confusion matrices, Precision, Recall, and mAP50 / mAP50-95 per class.

---

## 9. Running Automated Tests

Run the complete test suite:
```bash
pytest tests/test_backend.py -v
```

All 12 automated unit and integration tests validate:
- Configuration and runtime directory integrity
- Database schemas (Sessions, Tracked Entities, Alerts)
- Geometric computations (IoU, containment, Euclidean distance)
- Kalman multi-person tracking lifecycle
- Model manager loading and fallback
- FastAPI health and telemetry routes
- Video upload list and dataset inspection
- Video processing pipeline start/stop operations
