import os
import shutil
import subprocess
import time
import tempfile

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TEMP_DIR = tempfile.gettempdir()
DEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "visualizations", "output_screenshots"))
os.makedirs(DEST_DIR, exist_ok=True)

PAGES = [
    {
        "name": "01_dashboard_realtime_overview.png",
        "url": "http://localhost:3000/dashboard",
        "title": "Real-Time Field Telemetry & Sensor Analytics Dashboard",
        "window_size": "1600,1100"
    },
    {
        "name": "02_ml_model_evaluation_metrics.png",
        "url": "http://localhost:3000/metrics",
        "title": "ML Model Success Metrics & Comparative Evaluation Suite",
        "window_size": "1600,1200"
    },
    {
        "name": "03_autonomous_irrigation_controller.png",
        "url": "http://localhost:3000/irrigation",
        "title": "Autonomous Smart Irrigation & Hydrogel Retention Controller",
        "window_size": "1600,1150"
    },
    {
        "name": "04_soil_analysis_crop_suitability.png",
        "url": "http://localhost:3000/soil",
        "title": "Soil NPK Fertility Analysis & Crop Suitability Recommender",
        "window_size": "1600,1100"
    },
    {
        "name": "05_reports_and_water_audit.png",
        "url": "http://localhost:3000/reports",
        "title": "Historical Agronomic Reports & Water Conservation Audit",
        "window_size": "1600,1100"
    },
    {
        "name": "06_system_portal_landing.png",
        "url": "http://localhost:3000/",
        "title": "IrrigateWise System Portal & Cyber-Physical Architecture",
        "window_size": "1600,1100"
    }
]

def capture_all():
    print(f"Starting UI screenshot capture using headless Chrome...")
    for page in PAGES:
        temp_file = os.path.join(TEMP_DIR, f"temp_{page['name']}")
        dest_file = os.path.join(DEST_DIR, page["name"])
        
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
                
        cmd = [
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--window-size={page['window_size']}",
            "--virtual-time-budget=6000",
            f"--screenshot={temp_file}",
            page["url"]
        ]
        
        print(f"Capturing: {page['title']} from {page['url']}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        time.sleep(2)
        
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 1000:
            shutil.copy2(temp_file, dest_file)
            size_kb = os.path.getsize(dest_file) / 1024
            print(f"  [OK] Saved: {dest_file} ({size_kb:.1f} KB)")
        else:
            print(f"  [ERROR] Failed to capture {page['name']}: {result.stderr}")

if __name__ == "__main__":
    capture_all()
    print("\nAll UI screenshots captured successfully!")
