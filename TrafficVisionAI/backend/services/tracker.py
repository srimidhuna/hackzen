import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2
import time
import subprocess
from ultralytics import YOLO

# Global dictionary to store statistics per video process
video_stats = {}

# Define COCO classes matching required vehicles
VEHICLE_CLASSES = {
    1: 'Bicycle',
    2: 'Car',
    3: 'Motorcycle',
    5: 'Bus',
    7: 'Truck'
}

def get_ffmpeg_path():
    """Get the ffmpeg binary path from imageio-ffmpeg package."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"  # fallback to system ffmpeg

def get_yolo_model():
    """Load YOLOv8s. It will be downloaded automatically if not present."""
    return YOLO("yolov8s.pt")

def _reencode_to_h264(input_avi: str, output_mp4: str):
    """Re-encode an OpenCV-written AVI file to browser-compatible H.264 MP4."""
    ffmpeg = get_ffmpeg_path()
    cmd = [
        ffmpeg, "-y",
        "-i", input_avi,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_mp4
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except Exception as e:
        # If ffmpeg fails, just rename the avi as a fallback
        import shutil
        shutil.copy2(input_avi, output_mp4)
    finally:
        # Clean up temp avi
        if os.path.exists(input_avi):
            os.remove(input_avi)

def process_video(video_id: str, input_path: str, output_path: str):
    """
    Process video with YOLOv8x and ByteTrack.
    Writes annotated frames to a temp AVI, then re-encodes to browser-playable H.264 MP4.
    """
    model = get_yolo_model()

    # Initialize stats for this video
    video_stats[video_id] = {
        "status": "processing",
        "total_vehicles": 0,
        "counts": {
            "Car": 0,
            "Bus": 0,
            "Truck": 0,
            "Motorcycle": 0,
            "Bicycle": 0
        },
        "fps": 0,
        "progress": 0,
        "current_frame": 0,
        "total_frames": 0,
        "processing_time": 0,
        "unique_ids": set(),
        "recent_detections": [],
        "timeline": []
    }

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        video_stats[video_id]["status"] = "error"
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_stats[video_id]["total_frames"] = total_frames
    cap.release()

    # Write to a temporary AVI file first (reliable codec on all platforms)
    temp_avi_path = output_path.replace(".mp4", "_temp.avi")
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(temp_avi_path, fourcc, fps, (width, height))

    # Run tracking using BoT-SORT — heavily reduces ID switching for stationary objects
    results_generator = model.track(
        source=input_path,
        tracker="botsort.yaml",
        classes=list(VEHICLE_CLASSES.keys()),
        stream=True,
        verbose=False
    )

    frame_count = 0
    start_time = time.time()

    for results in results_generator:
        frame = results.orig_img.copy()
        frame_count += 1

        boxes = results.boxes
        if boxes is not None and boxes.id is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                track_id = int(box.id[0])

                label_name = VEHICLE_CLASSES.get(cls, "Unknown")

                # Update unique counts (each tracked ID counted only once)
                is_new = False
                if track_id not in video_stats[video_id]["unique_ids"]:
                    video_stats[video_id]["unique_ids"].add(track_id)
                    video_stats[video_id]["counts"][label_name] += 1
                    video_stats[video_id]["total_vehicles"] += 1
                    is_new = True

                if is_new or (frame_count % 30 == 0):
                    det_data = {
                        "id": track_id,
                        "type": label_name,
                        "conf": int(conf * 100),
                        "time": f"{int((frame_count/fps) // 60):02d}:{int((frame_count/fps) % 60):02d}",
                        "status": "Tracking"
                    }
                    # Update or append to recent detections (keep last 100 max)
                    existing = next((item for item in video_stats[video_id]["recent_detections"] if item["id"] == track_id), None)
                    if not existing:
                        video_stats[video_id]["recent_detections"].insert(0, det_data)
                        if len(video_stats[video_id]["recent_detections"]) > 100:
                            video_stats[video_id]["recent_detections"].pop()

                # --- Professional bounding box drawing ---
                # Box color per vehicle type
                colors = {
                    'Car': (72, 133, 237),       # Blue
                    'Bus': (244, 180, 0),        # Amber
                    'Truck': (15, 157, 88),      # Green
                    'Motorcycle': (219, 68, 55), # Red
                    'Bicycle': (170, 85, 255)    # Purple
                }
                color = colors.get(label_name, (0, 255, 0))

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # Label: "Car #14 (98%)"
                text = f"{label_name} #{track_id} ({int(conf * 100)}%)"
                (t_w, t_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                cv2.rectangle(frame, (x1, y1 - t_h - 10), (x1 + t_w + 6, y1), color, -1)
                cv2.putText(frame, text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        out.write(frame)

        # Update live stats periodically
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            current_fps = frame_count / elapsed if elapsed > 0 else 0
            video_stats[video_id]["fps"] = round(current_fps, 2)
            video_stats[video_id]["progress"] = round((frame_count / total_frames) * 100, 2) if total_frames > 0 else 0
            video_stats[video_id]["current_frame"] = frame_count
            
            # Record timeline every second roughly
            if frame_count % int(fps) == 0 or frame_count % 30 == 0:
                ts = f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
                video_stats[video_id]["timeline"].append({"time": ts, "count": video_stats[video_id]["total_vehicles"]})

    out.release()

    total_time = round(time.time() - start_time, 2)
    video_stats[video_id]["processing_time"] = total_time

    # Re-encode temp AVI → browser-compatible H.264 MP4
    _reencode_to_h264(temp_avi_path, output_path)

    video_stats[video_id]["status"] = "completed"
    video_stats[video_id]["progress"] = 100

def process_image(media_id: str, input_path: str, output_path: str):
    """
    Process a single image with YOLOv8s.
    Draws bounding boxes and tallies statistics for the frontend dashboard.
    """
    model = get_yolo_model()
    
    # Initialize stats for this media
    video_stats[media_id] = {
        "status": "processing",
        "total_vehicles": 0,
        "counts": {
            "Car": 0, "Bus": 0, "Truck": 0, "Motorcycle": 0, "Bicycle": 0
        },
        "fps": 0,
        "progress": 0,
        "processing_time": 0,
        "unique_ids": set()
    }
    
    start_time = time.time()
    
    # Run prediction
    results = model.predict(source=input_path, classes=list(VEHICLE_CLASSES.keys()), verbose=False)[0]
    frame = cv2.imread(input_path)
    
    boxes = results.boxes
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            label_name = VEHICLE_CLASSES.get(cls, "Unknown")
            video_stats[media_id]["counts"][label_name] += 1
            video_stats[media_id]["total_vehicles"] += 1
            
            # --- Professional bounding box drawing ---
            colors = { 'Car': (72, 133, 237), 'Bus': (244, 180, 0), 'Truck': (15, 157, 88), 'Motorcycle': (219, 68, 55), 'Bicycle': (170, 85, 255) }
            color = colors.get(label_name, (0, 255, 0))
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            text = f"{label_name} ({int(conf * 100)}%)"
            (t_w, t_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(frame, (x1, y1 - t_h - 10), (x1 + t_w + 6, y1), color, -1)
            cv2.putText(frame, text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            
    cv2.imwrite(output_path, frame)
    
    video_stats[media_id]["processing_time"] = round(time.time() - start_time, 2)
    video_stats[media_id]["status"] = "completed"
    video_stats[media_id]["progress"] = 100

def get_video_stats(video_id: str):
    stats = video_stats.get(video_id, None)
    if stats:
        res = dict(stats)
        res["unique_ids"] = list(stats["unique_ids"])
        return res
    return None

