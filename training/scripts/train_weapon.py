#!/usr/bin/env python3
"""
Custom Weapon Detection Model Training Pipeline (Module 2)
Trains YOLO11 on custom weapon datasets (Handgun, Rifle, Shotgun, Knife).
Generates mAP50, mAP50-95, precision, recall, and confusion matrix reports.
Exports validated weights to models/weapon/best.pt.
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path
import torch
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_weapon")

# Project root is 2 levels up from training/scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_YAML = PROJECT_ROOT / "training" / "datasets" / "weapons" / "data.yaml"
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "models" / "weapon" / "best.pt"
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "training" / "reports"

def parse_args():
    parser = argparse.ArgumentParser(description="Train Custom YOLO Weapon Detector")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA_YAML), help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (e.g. 8 for 4GB VRAM, 16 for 6GB RTX 4050)")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size for training")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="Base pretrained YOLO model (yolo11n.pt, yolo11s.pt)")
    parser.add_argument("--device", type=str, default="auto", help="Compute device: 'auto', '0', 'cuda', or 'cpu'")
    parser.add_argument("--lr0", type=float, default=0.01, help="Initial learning rate")
    parser.add_argument("--patience", type=int, default=15, help="Early stopping patience")
    parser.add_argument("--fraction", type=float, default=1.0, help="Fraction of dataset to use (e.g. 0.03 for fast CPU training)")
    parser.add_argument("--name", type=str, default="weapon_run", help="Training experiment run name")
    return parser.parse_args()

def check_dataset_readiness(data_yaml_path: Path):
    """Verifies that the dataset configuration exists and contains images."""
    if not data_yaml_path.exists():
        logger.error(f"data.yaml not found at {data_yaml_path}")
        return False

    weapons_dir = data_yaml_path.parent
    train_images_dir = weapons_dir / "train" / "images"
    val_images_dir = weapons_dir / "val" / "images"

    if not train_images_dir.exists() or len(list(train_images_dir.glob("*.*"))) == 0:
        logger.warning(
            f"No training images found in {train_images_dir}. "
            "Please populate training images and labels before starting training."
        )
        return False

    if not val_images_dir.exists() or len(list(val_images_dir.glob("*.*"))) == 0:
        logger.warning(
            f"No validation images found in {val_images_dir}. "
            "Validation set is required for mAP calculation and early stopping."
        )
        return False

    return True

def main():
    args = parse_args()
    data_yaml = Path(args.data).resolve()

    logger.info("=" * 65)
    logger.info("AI-POWERED ARMED HUMAN DETECTION: CUSTOM WEAPON MODEL TRAINING")
    logger.info("=" * 65)
    logger.info(f"Base Pretrained Model : {args.model}")
    logger.info(f"Dataset Configuration : {data_yaml}")
    logger.info(f"Target Classes        : Handgun (0), Rifle (1), Shotgun (2), Knife (3)")
    logger.info(f"Hyperparameters       : {args.epochs} epochs | Batch: {args.batch} | Image Size: {args.imgsz}")

    # Device selection
    if args.device == "auto":
        device = "0" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    if device != "cpu" and torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"Compute Device        : CUDA ({gpu_name})")
    else:
        logger.info("Compute Device        : CPU (CUDA not active)")

    # Validate dataset presence
    if not check_dataset_readiness(data_yaml):
        logger.info("\n[Dataset Preparation Guide]:")
        logger.info("1. Place training images in:  training/datasets/weapons/train/images/")
        logger.info("2. Place training labels in:  training/datasets/weapons/train/labels/")
        logger.info("3. Place validation images in: training/datasets/weapons/val/images/")
        logger.info("4. Place validation labels in: training/datasets/weapons/val/labels/")
        logger.info("5. Include negative images (people with cellphones/tools) without labels.")
        logger.info("\nRefer to training/DATASET_TRAINING_GUIDE.md for download sources and full steps.")
        sys.exit(1)

    # Initialize YOLO Model
    logger.info(f"\nInitializing YOLO model from {args.model}...")
    model = YOLO(args.model)

    # Training execution
    runs_dir = PROJECT_ROOT / "training" / "runs"
    logger.info("Starting training execution...")
    try:
        results = model.train(
            data=str(data_yaml),
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=device,
            lr0=args.lr0,
            patience=args.patience,
            fraction=args.fraction,
            project=str(runs_dir),
            name=args.name,
            exist_ok=True,
            plots=True,
            save=True,
            val=True
        )

        logger.info("\nTraining completed successfully!")

        # Export best weights to models/weapon/best.pt
        best_weights = runs_dir / args.name / "weights" / "best.pt"
        if best_weights.exists():
            DEFAULT_EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(best_weights, DEFAULT_EXPORT_PATH)
            logger.info(f"Exported validated weights to: {DEFAULT_EXPORT_PATH}")

        # Copy evaluation reports
        DEFAULT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        run_folder = runs_dir / args.name
        for report_file in ["confusion_matrix.png", "results.png", "PR_curve.png", "F1_curve.png"]:
            src = run_folder / report_file
            if src.exists():
                shutil.copy(src, DEFAULT_REPORTS_DIR / report_file)
                logger.info(f"Saved evaluation report: {DEFAULT_REPORTS_DIR / report_file}")

        # Print Final Metrics Summary
        logger.info("\n" + "=" * 65)
        logger.info("FINAL VALIDATION EVALUATION METRICS:")
        logger.info("=" * 65)
        if hasattr(results, "results_dict"):
            for k, v in results.results_dict.items():
                logger.info(f"  {k:25s} : {v:.4f}")

    except Exception as e:
        logger.error(f"Training interrupted with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
