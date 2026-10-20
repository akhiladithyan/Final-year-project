#!/usr/bin/env python3
"""
Custom Weapon Model Validation Pipeline (Module 2)
Computes Precision, Recall, mAP50, and mAP50-95 per class.
Generates confusion matrix and saves evaluation reports to training/reports/.
"""

import sys
import argparse
import logging
from pathlib import Path
import torch
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_weapon")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_WEIGHTS = PROJECT_ROOT / "models" / "weapon" / "best.pt"
DEFAULT_DATA_YAML = PROJECT_ROOT / "training" / "datasets" / "weapons" / "data.yaml"
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "training" / "reports"

def parse_args():
    parser = argparse.ArgumentParser(description="Validate Custom Weapon Detection Model")
    parser.add_argument("--weights", type=str, default=str(DEFAULT_WEIGHTS), help="Path to model weights (.pt)")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA_YAML), help="Path to data.yaml")
    parser.add_argument("--split", type=str, default="val", choices=["val", "test"], help="Dataset split to evaluate")
    parser.add_argument("--imgsz", type=int, default=640, help="Evaluation image size")
    parser.add_argument("--device", type=str, default="auto", help="Compute device ('auto', '0', 'cpu')")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold for validation")
    return parser.parse_args()

def main():
    args = parse_args()
    weights_path = Path(args.weights).resolve()
    data_yaml = Path(args.data).resolve()

    logger.info("=" * 65)
    logger.info("CUSTOM WEAPON MODEL VALIDATION & METRIC BENCHMARKING")
    logger.info("=" * 65)
    logger.info(f"Model Weights       : {weights_path}")
    logger.info(f"Dataset             : {data_yaml} ({args.split} split)")

    if not weights_path.exists():
        logger.error(
            f"Weights file not found at {weights_path}. "
            "Please train the model first using training/scripts/train_weapon.py "
            "or load pre-trained weights."
        )
        sys.exit(1)

    device = "0" if (args.device == "auto" and torch.cuda.is_available()) else ("cpu" if args.device == "auto" else args.device)

    # Load Model
    model = YOLO(str(weights_path))

    # Run Validation
    logger.info(f"Running validation on {args.split} set using device: {device}...")
    metrics = model.val(
        data=str(data_yaml),
        split=args.split,
        imgsz=args.imgsz,
        device=device,
        conf=args.conf,
        plots=True,
        project=str(DEFAULT_REPORTS_DIR),
        name="validation_results",
        exist_ok=True
    )

    logger.info("\n" + "=" * 65)
    logger.info("VALIDATION RESULTS SUMMARY:")
    logger.info("=" * 65)

    # Overall Metrics
    mp, mr, map50, map50_95 = metrics.box.mean_results()
    logger.info(f"Mean Precision (P) : {mp * 100:.2f}%")
    logger.info(f"Mean Recall (R)    : {mr * 100:.2f}%")
    logger.info(f"mAP@50             : {map50 * 100:.2f}%")
    logger.info(f"mAP@50-95          : {map50_95 * 100:.2f}%")

    logger.info("\nPer-Class Breakdown:")
    logger.info("-" * 65)
    logger.info(f"{'Class':<15} {'Precision':<12} {'Recall':<12} {'mAP50':<12} {'mAP50-95':<12}")
    logger.info("-" * 65)

    names = model.names
    for i, c in enumerate(metrics.box.ap_class_index):
        cls_name = names.get(c, f"Class {c}")
        p = metrics.box.p[i]
        r = metrics.box.r[i]
        ap50 = metrics.box.ap50[i]
        ap = metrics.box.ap[i]
        logger.info(f"{cls_name:<15} {p*100:<11.1f}% {r*100:<11.1f}% {ap50*100:<11.1f}% {ap*100:<11.1f}%")

    logger.info("-" * 65)
    logger.info(f"Confusion matrix & plots saved to: {DEFAULT_REPORTS_DIR / 'validation_results'}")

if __name__ == "__main__":
    main()
