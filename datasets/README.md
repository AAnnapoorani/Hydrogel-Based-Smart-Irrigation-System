# IRRIGATEWISE — Master Dataset Directory & External Links

This directory unifies all datasets required for the **IRRIGATEWISE Smart Terrace Garden Intelligence & Predictive Irrigation System**.

---

## 📁 Directory Structure & Local Datasets

```text
datasets/
├── botanical_catalog/
│   ├── terrace_plants_catalog.csv       <- 24 Curated container species with sunlight, volume, and hydrogel synergy
│   └── terrace_plants_catalog.json      <- Full botanical dictionary with Tamil names & care guides
├── moisture_iot/
│   └── sensor_timeseries_dataset.csv    <- 2,160 hourly readings (45-Day Trial: 15 Aug 2026 - 28 Sep 2026) comparing Hydrogel (25g/pot) vs Control
├── soil_and_crops/
│   ├── terrace_crop_recommendation.csv  <- 3,500 container garden records (14 terrace crops, 12 features with volume & hydrogel)
│   └── Crop_recommendation.csv          <- 3,500 Kaggle-format records (14 authentic terrace garden crops, N, P, K, pH, temp, humidity, rainfall, label)
├── plant_diseases/
│   ├── sample_test_images/              <- Real test leaf images for disease screening
│   └── (Full PlantVillage link below)
├── pests/
│   ├── sample_test_images/              <- Sample garden insect pest damage images
│   └── (Full IP102 link below)
├── download_image_datasets.py           <- Automated download helper
└── generate_terrace_crops.py            <- Script: scripts/generate_terrace_crops.py
```

---

## 🌐 External Dataset Sources & Direct Links

### 1. Foliar Plant Disease Image Dataset (Module 1)
* **Dataset Name:** PlantVillage Dataset
* **Official Authors:** Hughes & Salathé / Sharada P. Mohanty et al. (Penn State University & EPFL)
* **Direct Links:**
  - **Kaggle (Direct Download):** [Kaggle PlantVillage Dataset](https://www.kaggle.com/datasets/emmarex/plantdisease)
  - **GitHub Repository (Full Open Access):** [https://github.com/spMohanty/PlantVillage-Dataset](https://github.com/spMohanty/PlantVillage-Dataset)
  - **HuggingFace Hub:** [https://huggingface.co/datasets/plant_village](https://huggingface.co/datasets/plant_village)
* **Details:** 54,306 images across 38 crop disease categories. Includes Tomato Early Blight, Late Blight, Bacterial Spot, Mosaic Virus, Septoria, and Healthy leaves.

---

### 2. Crop Insect Pest Dataset (Module 2)
* **Dataset Name:** IP102: A Large-Scale Benchmark Dataset for Insect Pest Recognition
* **Official Authors:** Xiaoping Wu et al. (CVPR 2019)
* **Direct Links:**
  - **Official GitHub:** [https://github.com/xpwu95/IP102](https://github.com/xpwu95/IP102)
  - **Kaggle Mirror:** [Kaggle IP102 Insect Pest Dataset](https://www.kaggle.com/datasets/vencerlanz09/ip102-dataset)
* **Details:** 75,222 images across 102 pest categories. Contains Aphids, Whiteflies, Two-Spotted Spider Mites, Mealybugs, and Leaf Miners.

---

### 3. Terrace Garden Crop Suitability & Potting Mix Dataset (Module 3 & ML Classifier)
* **Dataset Name:** IRRIGATEWISE Terrace Container Crop Suitability Dataset
* **Generator Script:** [`scripts/generate_terrace_crops.py`](../scripts/generate_terrace_crops.py)
* **Local Copies:**
  - `datasets/soil_and_crops/terrace_crop_recommendation.csv` (Full 12-feature container mix dataset with container volume & hydrogel dosage)
  - `datasets/soil_and_crops/Crop_recommendation.csv` (Standard 8-column format: N, P, K, temperature, humidity, pH, rainfall, label)
* **Details:** 3,500 records (250 per class) covering 14 authentic terrace garden crops matching ICAR & TNAU rooftop container gardening standards:
  1. Bush Tomato (Potted Tomato)
  2. Cherry Tomato
  3. Green Chilli
  4. Capsicum (Bell Pepper)
  5. Brinjal (Eggplant)
  6. Okra (Lady's Finger)
  7. Bush French Beans
  8. Amaranth Keerai (Cheera)
  9. Indian Spinach (Palak)
  10. Spearmint (Pudina)
  11. Coriander (Kotthmalli)
  12. Curry Leaf (Kariveppilai)
  13. White Radish (Mullangi)
  14. Strawberry
* **ML Benchmark:** Random Forest classifier achieves **81.0% test accuracy** and **0.808 weighted F1-score** across 700 held-out test evaluations.

---

### 4. Soil Moisture & Hydrogel Telemetry Timeseries (Module 6 & Prediction Engine)
* **Dataset Name:** IRRIGATEWISE 45-Day Physics-Informed Terrace Container Timeseries (15 Aug 2026 – 28 Sep 2026)
* **Generator Source:** [`scripts/generate_terrace_dataset.py`](../scripts/generate_terrace_dataset.py) / [`backend/ml/generate_dataset.py`](../backend/ml/generate_dataset.py)
* **Local Copy:** Stored directly at `datasets/moisture_iot/sensor_timeseries_dataset.csv`
* **Ground Truth Source for Real Hardware:**
  - Connect your physical ESP32 node running capacitive sensor probes in your 10 × 15L grow bags.
  - The backend endpoint `POST /api/v1/sensors/readings` records real readings directly into the PostgreSQL database.
* **Open Meteorological Benchmark API:**
  - **Open-Meteo Historical & Real-Time Weather:** [https://open-meteo.com/](https://open-meteo.com/) (lat: 12.92, lon: 80.08 for Chennai/Tambaram).

---

### 5. Botanical Potting Mix & Container Standards (Modules 3 & 4)
* **TNAU Urban Horticulture Manual:** [Tamil Nadu Agricultural University Rooftop Garden Guide](https://agritech.tnau.ac.in/horticulture/horti_rooftop_vegetable_garden.html)
* **ICAR-IIHR Container Compendium:** [Indian Institute of Horticultural Research, Bengaluru](https://iihr.res.in/)
* **Local Structured Catalog:** Stored directly at `datasets/botanical_catalog/terrace_plants_catalog.json` and `.csv`.
