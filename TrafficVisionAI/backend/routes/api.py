from fastapi import APIRouter, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
import os
import uuid
import shutil
from backend.services.tracker import process_video, get_video_stats
from backend.services.analytics import generate_analytics_summary
from backend.services.report import generate_pdf_report, generate_json_report

router = APIRouter(prefix="/api")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

@router.post("/upload")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1].lower()
    
    is_image = ext in ["jpg", "jpeg", "png", "webp"]
    input_path = os.path.join(VIDEOS_DIR, f"{video_id}.{ext}")
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    if is_image:
        output_path = os.path.join(OUTPUTS_DIR, f"{video_id}.jpg")
        from backend.services.tracker import process_image
        background_tasks.add_task(process_image, video_id, input_path, output_path)
    else:
        output_path = os.path.join(OUTPUTS_DIR, f"{video_id}.mp4")
        background_tasks.add_task(process_video, video_id, input_path, output_path)
    
    return {"video_id": video_id, "type": "image" if is_image else "video", "message": "Processing started"}

@router.get("/statistics/{video_id}")
async def get_statistics(video_id: str):
    stats = get_video_stats(video_id)
    if not stats:
        return JSONResponse(status_code=404, content={"error": "Video stats not found"})
        
    if stats["status"] in ["completed", "processing"]:
        analytics = generate_analytics_summary(stats["counts"], stats["total_vehicles"])
        
        return {
            "status": stats["status"],
            "progress": stats["progress"],
            "fps": stats["fps"],
            "current_frame": stats.get("current_frame", 0),
            "total_frames": stats.get("total_frames", 0),
            "processing_time": stats.get("processing_time", 0),
            "analytics": analytics,
            "recent_detections": stats.get("recent_detections", [])[:20],
            "timeline": stats.get("timeline", [])[-30:]
        }
    return JSONResponse(status_code=400, content={"error": stats.get("status", "error")})

@router.get("/download/{video_id}/original")
async def download_original(video_id: str):
    """Serve the original uploaded video for split-screen comparison."""
    for ext in ["mp4", "avi", "mov", "mkv"]:
        path = os.path.join(VIDEOS_DIR, f"{video_id}.{ext}")
        if os.path.exists(path):
            return FileResponse(path, media_type="video/mp4", filename=f"Original_{video_id}.{ext}")
    return JSONResponse(status_code=404, content={"error": "Original video not found"})

@router.get("/download/{video_id}/video")
async def download_video(video_id: str):
    output_path = os.path.join(OUTPUTS_DIR, f"{video_id}.mp4")
    if not os.path.exists(output_path):
        return JSONResponse(status_code=404, content={"error": "Video not found or not processed"})
    return FileResponse(output_path, media_type="video/mp4", filename=f"TrafficVision_{video_id}.mp4")

@router.get("/download/{video_id}/image")
async def download_image(video_id: str):
    output_path = os.path.join(OUTPUTS_DIR, f"{video_id}.jpg")
    if not os.path.exists(output_path):
        return JSONResponse(status_code=404, content={"error": "Image not found or not processed"})
    return FileResponse(output_path, media_type="image/jpeg", filename=f"TrafficVision_{video_id}.jpg")

@router.get("/download/{video_id}/report")
async def download_report(video_id: str):
    stats = get_video_stats(video_id)
    if not stats or stats["status"] != "completed":
        return JSONResponse(status_code=400, content={"error": "Report not ready"})
        
    report_path = os.path.join(REPORTS_DIR, f"{video_id}.pdf")
    if not os.path.exists(report_path):
        generate_pdf_report(stats, report_path)
        
    return FileResponse(report_path, media_type="application/pdf", filename=f"TrafficReport_{video_id}.pdf")

@router.get("/download/{video_id}/json")
async def download_json(video_id: str):
    stats = get_video_stats(video_id)
    if not stats or stats["status"] != "completed":
        return JSONResponse(status_code=400, content={"error": "Report not ready"})
        
    json_path = os.path.join(REPORTS_DIR, f"{video_id}.json")
    if not os.path.exists(json_path):
        generate_json_report(stats, json_path)
        
    return FileResponse(json_path, media_type="application/json", filename=f"DetectionData_{video_id}.json")
