import cv2
import numpy as np
from pathlib import Path

def create_sample_video():
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "data" / "videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "sample_surveillance.mp4"

    width, height = 640, 480
    fps = 20
    duration_sec = 6
    total_frames = fps * duration_sec

    # OpenCV VideoWriter with mp4v codec
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for f in range(total_frames):
        # Create dark CCTV-style room frame
        frame = np.full((height, width, 3), 35, dtype=np.uint8)
        
        # Draw surveillance grid floor
        for y in range(300, height, 40):
            cv2.line(frame, (0, y), (width, y), (50, 50, 50), 1)

        # Draw a simulated walking person moving horizontally across the screen
        t = f / float(total_frames)
        person_x = int(50 + t * 450)
        person_y = 280

        # Head
        cv2.circle(frame, (person_x, person_y - 120), 22, (200, 200, 200), -1)
        # Torso
        cv2.rectangle(frame, (person_x - 25, person_y - 95), (person_x + 25, person_y), (180, 150, 100), -1)
        # Legs
        leg_offset = int(12 * np.sin(f * 0.5))
        cv2.line(frame, (person_x - 12, person_y), (person_x - 18 + leg_offset, person_y + 90), (120, 100, 80), 8)
        cv2.line(frame, (person_x + 12, person_y), (person_x + 18 - leg_offset, person_y + 90), (120, 100, 80), 8)
        # Arms
        arm_offset = int(15 * np.cos(f * 0.5))
        cv2.line(frame, (person_x - 25, person_y - 85), (person_x - 40 - arm_offset, person_y - 30), (200, 200, 200), 6)
        cv2.line(frame, (person_x + 25, person_y - 85), (person_x + 40 + arm_offset, person_y - 30), (200, 200, 200), 6)

        # CCTV timestamp overlay
        cv2.putText(
            frame,
            f"CAM-01 [TEST SURVEILLANCE] FRAME: {f:04d}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        out.write(frame)

    out.release()
    print(f"Sample video created successfully at: {video_path}")

    # Copy to uploads for immediate availability
    uploads_dir = project_root / "data" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(video_path, uploads_dir / "sample_surveillance.mp4")
    print(f"Sample video copied to uploads: {uploads_dir / 'sample_surveillance.mp4'}")

if __name__ == "__main__":
    create_sample_video()
