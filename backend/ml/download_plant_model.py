import os
import requests
import json

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts", "plant_disease_model")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

BASE_URL = "https://huggingface.co/imaflower/plantvillage-mobilenetv3/resolve/main"
FILES = ["model.onnx", "model.onnx.data", "class_names.json", "training_config.json"]

def download_plant_disease_model():
    print(f"Downloading PlantVillage MobileNetV3 ONNX Model to {ARTIFACTS_DIR}...")
    for filename in FILES:
        target_path = os.path.join(ARTIFACTS_DIR, filename)
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            print(f"  [OK] {filename} already exists ({os.path.getsize(target_path)/(1024*1024):.2f} MB)")
            continue
        url = f"{BASE_URL}/{filename}"
        print(f"  Downloading {filename} from {url}...")
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if isinstance(chunk, bytes):
                    f.write(chunk)
                elif chunk:
                    f.write(str(chunk).encode("utf-8"))
        print(f"  [DONE] Saved {filename} ({os.path.getsize(target_path)/(1024*1024):.2f} MB)")
    print("PlantVillage MobileNetV3 ONNX Model successfully downloaded and ready for inference!")

if __name__ == "__main__":
    download_plant_disease_model()
