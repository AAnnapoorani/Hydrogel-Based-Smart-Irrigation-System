"""
Automated End-to-End Verification Suite for IRRIGATEWISE Terrace Garden Modules
Tests all 7 newly implemented and integrated terrace gardening modules against
FastAPI backend and Next.js frontend.
"""

import urllib.request
import urllib.parse
import json
import io
from PIL import Image

BASE_BACKEND = "http://localhost:8000"
BASE_FRONTEND = "http://localhost:3000"

def log_test(module_name: str, passed: bool, detail: str):
    icon = "[PASS]" if passed else "[FAIL]"
    print(f"{icon} {module_name}: {detail}")
    assert passed, f"Test failed for {module_name}: {detail}"

def test_module_4_plant_recommender():
    payload = {
        "terrace_area_sqm": 20.0,
        "pot_count": 10,
        "sunlight_hours": "4-6h",
        "container_size_litres": 15.0,
        "soil_type": "cocopeat_mix",
        "season": "post_monsoon",
        "water_availability": "moderate",
        "experience_level": "beginner",
        "preferred_categories": ["vegetables", "herbs"],
        "maintenance_level": "moderate",
        "gardening_purposes": ["household_consumption", "cooking_herbs"],
        "hydrogel_present": True
    }
    req = urllib.request.Request(
        f"{BASE_BACKEND}/api/v1/terrace/recommend",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        passed = (
            resp.status == 200 and 
            len(data.get("recommended_plants", [])) > 0 and 
            "hydrogel_recommendation" in data
        )
        first_plant = data["recommended_plants"][0]["name"]
        log_test("Module 4 (Recommender)", passed, f"Recommended {len(data['recommended_plants'])} plants. Top: {first_plant}")

def test_catalog():
    with urllib.request.urlopen(f"{BASE_BACKEND}/api/v1/terrace/catalog") as resp:
        data = json.loads(resp.read().decode("utf-8"))
        passed = resp.status == 200 and data.get("total", 0) == 24
        log_test("Module 4 (Catalog)", passed, f"Loaded {data.get('total')} curated container species")

def test_module_3_soil_health():
    url = f"{BASE_BACKEND}/api/v1/terrace/soil/interpretation?nitrogen=90&phosphorus=45&potassium=210&ph=6.4&hydrogel_present=true"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        passed = (
            resp.status == 200 and 
            data.get("overall_fertility_index") > 0 and 
            len(data.get("readings", [])) == 4 and
            "Hydrogel" in data.get("hydrogel_retention_effect", "")
        )
        log_test("Module 3 (Soil Potting Mix)", passed, f"Grade: {data.get('fertility_grade')} ({data.get('overall_fertility_index')}/100)")

def test_module_5_plant_care_assistant():
    payload = {
        "plant_name": "Tomato",
        "growth_stage": "Flowering",
        "current_moisture": 51.0,
        "temperature": 32.0,
        "humidity": 68.0,
        "forecast_rain_mm": 0.0,
        "hydrogel_present": True,
        "yellowing_observed": False
    }
    req = urllib.request.Request(
        f"{BASE_BACKEND}/api/v1/terrace/care/advisory",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        passed = (
            resp.status == 200 and 
            data.get("watering_urgency") in ["Moderate Need", "Immediate Replenishment", "Not Needed"] and
            len(data.get("immediate_actions", [])) > 0
        )
        log_test("Module 5 (Care Assistant)", passed, f"Urgency: {data.get('watering_urgency')}, Vol: {data.get('watering_volume_ml')}mL")

def test_module_6_irrigation_intelligence():
    payload = {
        "current_moisture": 45.0,
        "target_moisture": 60.0,
        "temperature": 31.0,
        "humidity": 65.0,
        "crop_type": "Tomato",
        "field_area": 10.0,
        "pot_count": 10,
        "hydrogel_present": 1
    }
    req = urllib.request.Request(
        f"{BASE_BACKEND}/api/v1/irrigation/predict",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        passed = (
            resp.status == 200 and 
            "comparison" in data and 
            data["comparison"].get("water_saving_advantage_pct", 0) > 0
        )
        adv = data["comparison"]["water_saving_advantage_pct"]
        log_test("Module 6 (Irrigation Intelligence)", passed, f"Predictive Water Savings Advantage: {adv:.1f}%")

def test_module_7_plant_registry():
    # 1. List plants
    with urllib.request.urlopen(f"{BASE_BACKEND}/api/v1/terrace/plants") as resp:
        plants = json.loads(resp.read().decode("utf-8"))
        passed = resp.status == 200 and len(plants) > 0
        log_test("Module 7 (Plants Registry)", passed, f"Found {len(plants)} registered container plants")
        first_id = plants[0]["id"]

    # 2. Add an observation log
    obs_payload = {
        "plant_id": first_id,
        "observation_type": "Flowering",
        "notes": "Automated verification test observation: new vigorous bud cluster observed.",
        "severity": "Normal"
    }
    req = urllib.request.Request(
        f"{BASE_BACKEND}/api/v1/terrace/plants/{first_id}/observations",
        data=json.dumps(obs_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        obs_data = json.loads(resp.read().decode("utf-8"))
        passed_obs = resp.status == 200 and obs_data.get("observation_type") == "Flowering"
        log_test("Module 7 (Observation Logbook)", passed_obs, f"Logged observation ID: {obs_data.get('id')}")

def test_module_1_and_2_diagnosis():
    # Generate in-memory synthetic leaf image
    img = Image.new("RGB", (300, 300), color=(50, 180, 50))
    # Add a yellow spot for chlorosis
    for x in range(120, 180):
        for y in range(120, 180):
            img.putpixel((x, y), (220, 200, 40))
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    image_bytes = buf.getvalue()

    # Construct multipart form-data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="test_leaf.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + image_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    # 1. Disease Diagnosis
    req_disease = urllib.request.Request(
        f"{BASE_BACKEND}/api/v1/terrace/diagnosis/disease",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req_disease) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        passed_disease = resp.status == 200 and "primary_condition" in data and len(data.get("verification_steps", [])) > 0
        log_test("Module 1 (Disease Diagnosis)", passed_disease, f"Diagnosed: {data.get('primary_condition')} (Confidence: {data.get('confidence')})")

    # 2. Pest Diagnosis
    req_pest = urllib.request.Request(
        f"{BASE_BACKEND}/api/v1/terrace/diagnosis/pest",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req_pest) as resp:
        data_pest = json.loads(resp.read().decode("utf-8"))
        passed_pest = resp.status == 200 and "primary_pest" in data_pest and len(data_pest.get("organic_management", [])) > 0
        log_test("Module 2 (Pest Identification)", passed_pest, f"Primary Pest: {data_pest.get('primary_pest')} (Type: {data_pest.get('detection_type')})")

def test_frontend_routes():
    routes = ["/", "/dashboard", "/recommender", "/diagnosis", "/plants", "/soil"]
    for route in routes:
        url = f"{BASE_FRONTEND}{route}"
        with urllib.request.urlopen(url) as resp:
            passed = resp.status == 200
            log_test(f"Frontend Route ({route})", passed, f"HTTP Status {resp.status}")

def run_all():
    print("=" * 65)
    print("RUNNING IRRIGATEWISE TERRACE GARDEN VERIFICATION SUITE")
    print("=" * 65)
    test_module_4_plant_recommender()
    test_catalog()
    test_module_3_soil_health()
    test_module_5_plant_care_assistant()
    test_module_6_irrigation_intelligence()
    test_module_7_plant_registry()
    test_module_1_and_2_diagnosis()
    test_frontend_routes()
    print("=" * 65)
    print("ALL MODULE TESTS PASSED PERFECTLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_all()
