# TrafficVision AI — Intelligent Traffic Analytics

TrafficVision AI is an intelligent traffic monitoring and analytics system designed to detect, track, and analyze vehicles in video streams. By leveraging advanced Computer Vision and AI techniques, the system classifies vehicles, monitors traffic density, and generates actionable insights and reports.

## Features

- **Object Detection & Tracking:** Real-time detection of various vehicle classes (Car, Bus, Truck, Motorcycle, Bicycle).
- **Traffic Analytics:** Computes traffic density, identifies peak vehicle types, and generates AI-driven traffic insights and recommendations.
- **Reporting:** Automatic generation of professional PDF reports and JSON data files based on tracked traffic metrics.
- **Modern Dashboard:** An interactive web dashboard with dynamic data visualization and responsive UI.

## Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/):** High-performance backend API framework.
- **[Uvicorn](https://www.uvicorn.org/):** ASGI web server implementation for Python.
- **[OpenCV](https://opencv.org/):** Core library for image and video processing.
- **[ReportLab](https://www.reportlab.com/):** Tool for generating analytical PDF reports.
- **[Jinja2](https://jinja.palletsprojects.com/):** Templating engine for serving dynamic HTML.

### Frontend
- **HTML / CSS / JavaScript**
- **[Tailwind CSS](https://tailwindcss.com/):** Utility-first CSS framework for a modern, responsive design.
- **[Chart.js](https://www.chartjs.org/):** Library for creating dynamic data visualizations and charts.
- **[Lucide Icons](https://lucide.dev/):** Clean and consistent iconography.

## Third-Party Libraries & Pre-trained Models Acknowledgment

Proper acknowledgment goes to the developers and communities of the following tools and models:

- **[Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics):** Used as the core pre-trained model for real-time object detection and tracking (ByteTrack algorithm). The system automatically downloads the `yolov8s.pt` model weights for inference.
- **[COCO Dataset](https://cocodataset.org/):** The YOLOv8 model used in this project was pre-trained on the COCO (Common Objects in Context) dataset, which enables out-of-the-box recognition of the vehicle classes monitored.
- **[FFmpeg](https://ffmpeg.org/):** Utilized via `imageio-ffmpeg` to re-encode processed video feeds into browser-compatible H.264 formats.

## Project Setup

### Prerequisites
- Python 3.8+
- System installation of `ffmpeg` (recommended) or relies on `imageio-ffmpeg`.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AKALYA-1234/ParkVision-AI.git
   cd ParkVision-AI/TrafficVisionAI
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage Instructions

1. **Start the FastAPI server:**
   Ensure you are in the `TrafficVisionAI` directory, then run:
   ```bash
   python -m backend.main
   ```
   Or using Uvicorn directly:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the Dashboard:**
   Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

3. **Upload and Process Video:**
   - Use the dashboard interface to upload a traffic video.
   - The backend will process the video, perform vehicle detection/tracking, and update the analytics in real-time.
   - Once completed, you can view the traffic density, vehicle counts, and download PDF or JSON reports from the generated insights.

## Project Structure

```text
TrafficVisionAI/
├── backend/
│   ├── main.py          # FastAPI application entry point
│   ├── routes/          # API route definitions
│   └── services/        # Core logic (tracker, analytics, report generation)
├── frontend/
│   ├── static/          # Static assets (CSS, JS, Images)
│   └── templates/       # Jinja2 HTML templates (index.html)
├── reports/             # Generated PDF and JSON reports
├── outputs/             # Processed video outputs
├── videos/              # Uploaded video files
└── requirements.txt     # Python dependencies
```
