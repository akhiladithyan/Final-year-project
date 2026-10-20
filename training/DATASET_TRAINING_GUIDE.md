# Complete Dataset Preparation & Training Walkthrough

This document provides end-to-end instructions for preparing datasets, annotating custom images, training the YOLO weapon detection model (Module 2), evaluating metrics, and deploying the weights into the real-time surveillance dashboard.

---

## 1. Target Classes & Annotation Standards

The weapon detector is configured for four distinct classes:

| Class ID | Class Name | Description |
|---|---|---|
| `0` | **Handgun** | Revolvers, semi-automatic pistols, compact firearms |
| `1` | **Rifle** | Assault rifles, carbines, long-barrel automatic firearms |
| `2` | **Shotgun** | Pump-action, break-action, tactical shotguns |
| `3` | **Knife** | Combat knives, daggers, machetes, folding blades |

### YOLO Annotation Format
Each image in the dataset must have a corresponding `.txt` file with the identical filename in the `labels/` directory (e.g. `img_001.jpg` $\leftrightarrow$ `img_001.txt`).

Each line inside the `.txt` file defines one bounding box in normalized coordinates ($0.0 \text{ to } 1.0$):
```text
<class_id> <x_center> <y_center> <width> <height>
```
*Example line for a handgun located near center:*
```text
0 0.512400 0.634100 0.142000 0.228000
```

---

## 2. Dataset Sourcing Options

### Option A: Roboflow Universe (Recommended for quick start)
1. Search Roboflow Universe for:
   - "Weapons Detection YOLOv11"
   - "Gun and Knife Detection"
2. Filter for datasets with Handgun, Rifle, Knife.
3. Export the dataset in **YOLOv8 / YOLOv11 format**.
4. Download the zip archive and extract it directly into `training/datasets/weapons/`.

### Option B: Kaggle Weapon Detection Datasets
- Search for "Kaggle Gun and Weapon Detection" (contains over 5,000 labeled CCTV surveillance frames).
- Ensure class IDs match our `data.yaml` mapping.

### Option C: Open Images V7
- Extract classes `/m/0g49wd` (Handgun), `/m/061hd_` (Rifle), and `/m/04ctxx` (Knife) using FiftyOne or the Open Images downloader.

---

## 3. The Crucial Role of Negative (Background) Samples

> [!IMPORTANT]
> **To prevent false alarms in surveillance environments**, you MUST include **10% to 15% negative background images**.

Negative images should depict:
- People holding smartphones, wallets, power tools, water bottles, microphones, or umbrellas.
- Empty surveillance rooms, hallways, and entrance gates under different lighting conditions.

**How to format negative images:**
- Place the image in `train/images/` (e.g. `bg_phone_01.jpg`).
- Create an **empty** label file in `train/labels/` (e.g. `bg_phone_01.txt` with 0 bytes).
- Ultralytics YOLO will automatically recognize these as pure background images and penalize false positives.

---

## 4. Directory Layout

Organize your files as follows:

```text
training/datasets/weapons/
├── data.yaml
├── train/
│   ├── images/
│   │   ├── frame_001.jpg
│   │   ├── frame_002.jpg
│   │   └── bg_phone_01.jpg
│   └── labels/
│       ├── frame_001.txt
│       ├── frame_002.txt
│       └── bg_phone_01.txt  (0 bytes - negative sample)
├── val/
│   ├── images/
│   │   └── val_001.jpg
│   └── labels/
│       └── val_001.txt
└── test/
    ├── images/
    └── labels/
```

Verify `training/datasets/weapons/data.yaml`:
```yaml
path: ../training/datasets/weapons
train: train/images
val: val/images
test: test/images

names:
  0: Handgun
  1: Rifle
  2: Shotgun
  3: Knife
```

---

## 5. Running Model Training

### Command-Line Execution
Run the training script from the project root:

```bash
# Recommended for NVIDIA RTX 4050 (6GB VRAM):
python training/scripts/train_weapon.py --epochs 50 --batch 16 --imgsz 640 --model yolo11n.pt --device 0

# For CPU-only training:
python training/scripts/train_weapon.py --epochs 30 --batch 8 --imgsz 480 --model yolo11n.pt --device cpu
```

### Key Training Parameters Explained:
- `--epochs 50`: 50 passes over the dataset. Early stopping patience (15 epochs) will halt training if validation loss stops improving.
- `--batch 16`: Perfectly fits the 6GB VRAM of the NVIDIA RTX 4050 GPU. If out-of-memory occurs, reduce to `--batch 8`.
- `--imgsz 640`: Standard high-resolution size for small object detection (e.g. holstered handguns, pocket knives).
- `--model yolo11n.pt`: Starts from Ultralytics YOLO11 Nano pretrained weights (transfer learning accelerates convergence).

### Automatic Deployment:
Upon completion, the training script automatically:
1. Copies the top-performing weights (`best.pt`) to `models/weapon/best.pt`.
2. Generates evaluation graphs in `training/reports/`:
   - `confusion_matrix.png`
   - `PR_curve.png` (Precision-Recall curve)
   - `results.png` (Training and Validation loss curves)

---

## 6. Validation and Benchmarking

To validate existing or newly trained weights against the validation or test split:

```bash
python training/scripts/validate_weapon.py --weights models/weapon/best.pt --split val
```

This outputs per-class metrics:
- **Precision (P)**: Percentage of detected weapons that are actual weapons.
- **Recall (R)**: Percentage of all actual weapons correctly detected.
- **mAP@50**: Mean average precision at IoU threshold 0.50.
- **mAP@50-95**: Stricter composite average precision across IoU 0.50 to 0.95.

### Inference Latency Benchmark:
To test raw inference speed on your GPU:
```bash
python training/scripts/evaluate_model.py --weights models/weapon/best.pt --benchmark_frames 100
```
Expect **> 60 FPS** on NVIDIA GeForce RTX 4050.

---

## 7. Connecting with the Surveillance Dashboard

Once `models/weapon/best.pt` is generated:
1. Open the **Model Management** page in the dashboard.
2. The Weapon Detector status will automatically switch from `AWAITING TRAINING` to `WEIGHTS LOADED`.
3. In **Live Detection**, any detected Handgun, Rifle, Shotgun, or Knife will be:
   - Highlighted in red bounding boxes with confidence scores.
   - Associated with nearby human tracking IDs using spatial containment and wrist proximity.
   - Flagged with review banners (`ASSOCIATION PROBABLE` or `ASSOCIATION UNCERTAIN`).
