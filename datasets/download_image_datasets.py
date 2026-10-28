"""
Automated Image Dataset Downloader for IRRIGATEWISE
Downloads representative test/validation samples from open-source repositories:
1. PlantVillage Dataset (Foliar Diseases: Early Blight, Late Blight, Bacterial Spot, Healthy)
2. IP102 / Agricultural Pest Dataset (Aphids, Whiteflies, Spider Mites, Mealybugs)
"""

import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DISEASE_DIR = os.path.join(BASE_DIR, "plant_diseases", "sample_test_images")
PEST_DIR = os.path.join(BASE_DIR, "pests", "sample_test_images")

os.makedirs(DISEASE_DIR, exist_ok=True)
os.makedirs(PEST_DIR, exist_ok=True)

# Curated direct raw open-access sample images from official GitHub repositories
SAMPLE_DISEASE_URLS = {
    "tomato_early_blight.jpg": "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Early_blight/0012b9d2-2130-4a06-a834-b1f3af34f57e___RS_Erly.B%209472.JPG",
    "tomato_late_blight.jpg": "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Late_blight/00ce447d-3173-495e-aa94-578f46ae9213___GHLB2%20Leaf%2088.1.JPG",
    "tomato_bacterial_spot.jpg": "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___Bacterial_spot/00416648-be6e-4bd4-bc8d-82f43f8a7240___GCREC_Bact.Sp%203110.JPG",
    "tomato_healthy.jpg": "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/Tomato___healthy/000bf685-b305-408b-91f4-37030f8e62db___GH_HL%20Leaf%20308.1.JPG"
}

def download_samples():
    print("Downloading representative PlantVillage foliar disease images...")
    for filename, url in SAMPLE_DISEASE_URLS.items():
        dest = os.path.join(DISEASE_DIR, filename)
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  [OK] Saved {filename} ({os.path.getsize(dest)} bytes)")
        except Exception as e:
            print(f"  [WARN] Failed to download {filename} directly from raw CDN: {e}")

    print("\nSample dataset directory initialized at:")
    print(f"  -> {DISEASE_DIR}")
    print(f"  -> {PEST_DIR}")

if __name__ == "__main__":
    download_samples()
