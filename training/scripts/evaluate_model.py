#!/usr/bin/env python3
"""
Model Inference & Latency Evaluation Benchmarking Script
Tests model latency (ms per frame, throughput FPS) and saves visual detections.
"""

import time
import argparse
import logging
from pathlib import Path
import numpy as np
import cv2
import torch
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_model")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_WEIGHTS = PROJECT_ROOT / "models" / "weapon" / "best.pt"
OUTPUT_DIR = PROJECT_ROOT / "training" / "reports" / "evaluation_output"

def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate Model Latency & Visual Predictions")
    parser.add_argument("--weights", type=str, default=str(DEFAULT_WEIGHTS), help="Path to model weights (.pt)")
    parser.add_argument("--source", type=str, default="", help="Path to image file, image directory, or video")
    parser.add_argument("--conf", type=float, default=0.45, help="Confidence threshold")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference resolution")
    parser.add_argument("--device", type=str, default="auto", help="Compute device ('auto', '0', 'cpu')")
    parser.add_argument("--benchmark_frames", type=int, default=100, help="Number of synthetic frames for latency benchmarking")
    return parser.parse_args()

def run_latency_benchmark(model: YOLO, device: str, imgsz: int, num_frames: int):
    """Measures pure inference latency and throughput FPS on synthetic frames."""
    logger.info(f"\nBenchmarking inference latency on {num_frames} frames (size: {imgsz}x{imgsz})...")

    # Warmup
    dummy_frame = np.random.randint(0, 255, (imgsz, imgsz, 3), dtype=np.uint8)
    for _ in range(10):
        _ = model.predict(dummy_frame, device=device, verbose=False)

    latencies = []
    for _ in range(num_frames):
        t0 = time.perf_counter()
        _ = model.predict(dummy_frame, device=device, verbose=False)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms

    avg_ms = np.mean(latencies)
    std_ms = np.std(latencies)
    fps = 1000.0 / avg_ms

    logger.info("-" * 65)
    logger.info("HARDWARE INFERENCE LATENCY BENCHMARK RESULTS:")
    logger.info("-" * 65)
    logger.info(f"Average Inference Latency : {avg_ms:.2f} ms (+/- {std_ms:.2f} ms)")
    logger.info(f"Throughput FPS             : {fps:.1f} FPS")
    logger.info("-" * 65)

def main():
    args = parse_args()
    weights_path = Path(args.weights).resolve()

    if not weights_path.exists():
        logger.warning(f"Weights file not found at {weights_path}. Falling back to 'yolo11n.pt' for latency benchmark.")
        weights_to_load = "yolo11n.pt"
    else:
        weights_to_load = str(weights_path)

    device = "0" if (args.device == "auto" and torch.cuda.is_available()) else ("cpu" if args.device == "auto" else args.device)
    model = YOLO(weights_to_load)

    # 1. Latency Benchmark
    run_latency_benchmark(model, device, args.imgsz, args.benchmark_frames)

    # 2. Source Inference (if provided)
    if args.source and Path(args.source).exists():
        logger.info(f"\nRunning visual inference on source: {args.source}...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        results = model.predict(
            source=args.source,
            conf=args.conf,
            device=device,
            imgsz=args.imgsz,
            save=True,
            project=str(OUTPUT_DIR),
            name="visual_predictions",
            exist_ok=True
        )
        logger.info(f"Visual annotated detections saved to: {OUTPUT_DIR / 'visual_predictions'}")

if __name__ == "__main__":
    main()
