import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI application
app = FastAPI(title="TrafficVision AI - Intelligent Traffic Monitoring & Analytics")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define configuration paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# Ensure required directories exist
for directory in [VIDEOS_DIR, OUTPUTS_DIR, REPORTS_DIR, os.path.join(FRONTEND_DIR, "static"), os.path.join(FRONTEND_DIR, "templates")]:
    os.makedirs(directory, exist_ok=True)

# Mount static directories
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")
app.mount("/reports_files", StaticFiles(directory=REPORTS_DIR), name="reports_files")

# Set up templates
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

from backend.routes import api
app.include_router(api.router)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
