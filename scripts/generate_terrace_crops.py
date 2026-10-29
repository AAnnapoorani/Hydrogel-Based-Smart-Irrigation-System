"""Terrace Container Gardening Crop Suitability Dataset Generator.

Generates realistic agronomic profiles for 14 authentic terrace container garden
crops under Tamil Nadu / tropical rooftop conditions with Superabsorbent Polymer (SAP) Hydrogel.

Outputs:
1. datasets/soil_and_crops/terrace_crop_recommendation.csv (Full 12-feature container dataset)
2. datasets/soil_and_crops/Crop_recommendation.csv (Standard 8-column Kaggle-compatible format)
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(WORKSPACE_ROOT, "datasets", "soil_and_crops")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 14 Essential Terrace Container Garden Crops with Agronomic Distributions
# Format: (N_mean, N_std, P_mean, P_std, K_mean, K_std, pH_mean, pH_std, OC_mean, OC_std,
#          T_mean, T_std, H_mean, H_std, Rain_mean, Rain_std, Cont_mean, Cont_std, Hydro_mean, Hydro_std, Preferred_soil, soil_probs)
TERRACE_CROP_PROFILES = {
    "Bush Tomato": (
        115, 12, 55, 8, 220, 20, 6.4, 0.3, 1.10, 0.15,
        28, 3, 70, 7, 100, 20, 18, 3, 25, 4, ["loam", "clay", "sandy"], [0.65, 0.25, 0.10]
    ),
    "Cherry Tomato": (
        105, 10, 48, 7, 195, 18, 6.4, 0.3, 1.05, 0.12,
        26, 3, 65, 6, 85, 18, 12, 2, 20, 3, ["loam", "clay", "sandy"], [0.70, 0.20, 0.10]
    ),
    "Green Chilli": (
        90, 10, 42, 6, 150, 15, 6.5, 0.4, 0.85, 0.10,
        30, 4, 60, 8, 70, 15, 12, 2, 18, 3, ["loam", "sandy", "clay"], [0.60, 0.30, 0.10]
    ),
    "Capsicum": (
        105, 10, 50, 6, 185, 18, 6.6, 0.3, 0.95, 0.12,
        25, 3, 70, 6, 80, 15, 15, 3, 22, 3, ["loam", "clay", "sandy"], [0.65, 0.25, 0.10]
    ),
    "Brinjal": (
        110, 12, 48, 7, 170, 18, 6.6, 0.4, 1.00, 0.14,
        29, 3, 68, 7, 95, 20, 18, 3, 25, 4, ["loam", "clay", "sandy"], [0.60, 0.30, 0.10]
    ),
    "Okra": (
        75, 9, 35, 5, 125, 14, 6.8, 0.4, 0.75, 0.10,
        32, 4, 58, 8, 75, 18, 14, 2, 20, 3, ["loam", "sandy", "clay"], [0.55, 0.30, 0.15]
    ),
    "Bush French Beans": (
        45, 7, 50, 7, 105, 12, 6.4, 0.3, 0.85, 0.12,
        24, 3, 62, 6, 65, 15, 12, 2, 15, 3, ["loam", "sandy", "clay"], [0.65, 0.25, 0.10]
    ),
    "Amaranth Keerai": (
        100, 10, 30, 5, 115, 12, 6.7, 0.4, 1.10, 0.15,
        31, 3, 72, 7, 70, 15, 8, 2, 12, 2, ["loam", "clay", "sandy"], [0.60, 0.25, 0.15]
    ),
    "Indian Spinach": (
        95, 10, 35, 5, 110, 12, 6.6, 0.3, 1.15, 0.15,
        25, 3, 75, 6, 60, 12, 10, 2, 15, 2, ["loam", "clay", "sandy"], [0.70, 0.20, 0.10]
    ),
    "Spearmint": (
        80, 9, 28, 4, 90, 10, 6.5, 0.3, 1.20, 0.16,
        26, 3, 72, 7, 50, 10, 8, 2, 15, 2, ["loam", "clay", "sandy"], [0.70, 0.20, 0.10]
    ),
    "Coriander": (
        65, 8, 26, 4, 80, 10, 6.6, 0.3, 0.90, 0.12,
        23, 3, 62, 6, 45, 10, 6, 1, 10, 2, ["loam", "sandy", "clay"], [0.65, 0.25, 0.10]
    ),
    "Curry Leaf": (
        78, 9, 35, 5, 135, 15, 6.8, 0.4, 0.95, 0.14,
        31, 4, 60, 8, 90, 20, 25, 4, 30, 5, ["loam", "clay", "sandy"], [0.60, 0.25, 0.15]
    ),
    "White Radish": (
        60, 8, 48, 6, 130, 14, 6.4, 0.3, 0.80, 0.10,
        23, 3, 60, 6, 50, 12, 16, 3, 15, 3, ["sandy", "loam", "clay"], [0.55, 0.35, 0.10]
    ),
    "Strawberry": (
        55, 7, 55, 7, 175, 18, 6.0, 0.3, 1.30, 0.18,
        21, 3, 68, 6, 40, 10, 10, 2, 18, 3, ["loam", "sandy", "clay"], [0.65, 0.25, 0.10]
    )
}

def generate_terrace_crop_datasets(samples_per_crop: int = 250):
    rows_full = []
    rows_standard = []
    
    for crop, prof in TERRACE_CROP_PROFILES.items():
        (n_m, n_s, p_m, p_s, k_m, k_s, ph_m, ph_s, oc_m, oc_s,
         t_m, t_s, h_m, h_s, r_m, r_s, c_m, c_s, hy_m, hy_s, soils, soil_probs) = prof
        
        for _ in range(samples_per_crop):
            n = round(float(np.clip(np.random.normal(n_m, n_s), 15, 180)), 1)
            p = round(float(np.clip(np.random.normal(p_m, p_s), 10, 100)), 1)
            k = round(float(np.clip(np.random.normal(k_m, k_s), 40, 320)), 1)
            ph = round(float(np.clip(np.random.normal(ph_m, ph_s), 4.8, 8.5)), 2)
            oc = round(float(np.clip(np.random.normal(oc_m, oc_s), 0.25, 2.0)), 2)
            temp = round(float(np.clip(np.random.normal(t_m, t_s), 15, 42)), 2)
            hum = round(float(np.clip(np.random.normal(h_m, h_s), 30, 95)), 2)
            rain = round(float(np.clip(np.random.normal(r_m, r_s), 10, 250)), 2)
            soil = str(np.random.choice(soils, p=soil_probs))
            vol = round(float(np.clip(np.random.normal(c_m, c_s), 4, 45)), 1)
            hydro = round(float(np.clip(np.random.normal(hy_m, hy_s), 5, 50)), 1)
            
            # 1. Full 12-feature terrace container dataset
            rows_full.append({
                "nitrogen": n,
                "phosphorus": p,
                "potassium": k,
                "ph": ph,
                "organic_carbon": oc,
                "temperature": temp,
                "humidity": hum,
                "rainfall": rain,
                "soil_type": soil,
                "container_volume_litres": vol,
                "hydrogel_dosage_g": hydro,
                "crop": crop
            })
            
            # 2. Standard 8-column format (N,P,K,temperature,humidity,ph,rainfall,label)
            rows_standard.append({
                "N": int(round(n)),
                "P": int(round(p)),
                "K": int(round(k)),
                "temperature": temp,
                "humidity": hum,
                "ph": ph,
                "rainfall": rain,
                "label": crop.lower().replace(" ", "_")
            })

    df_full = pd.DataFrame(rows_full)
    df_standard = pd.DataFrame(rows_standard)
    
    # Save full terrace dataset
    terrace_path = os.path.join(OUTPUT_DIR, "terrace_crop_recommendation.csv")
    df_full.to_csv(terrace_path, index=False)
    print(f"Generated {len(df_full)} rows -> {terrace_path}")
    
    # Save standard format dataset
    std_path = os.path.join(OUTPUT_DIR, "Crop_recommendation.csv")
    df_standard.to_csv(std_path, index=False)
    print(f"Updated {len(df_standard)} rows -> {std_path}")

if __name__ == "__main__":
    generate_terrace_crop_datasets(samples_per_crop=250)
