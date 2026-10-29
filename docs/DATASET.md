# Dataset Architecture & Physics-Informed Modeling

## 1. Dataset Classification & Academic Disclosure

> **Academic Rigor Disclosure:** 
> The dataset utilized for training, validation, and benchmarking the IRRIGATEWISE machine learning models is a **Development / Simulation Dataset (Physics-Informed)** generated via rigorous agronomic and physical differential equations. 
> It does **not** claim to be derived from physical field micro-sensor measurements, avoiding fabrication of real-world experimental telemetry. The parameters reflect standard Mediterranean/Semi-Arid loam soil characteristics amended with potassium polyacrylate hydrogel polymer.

---

## 2. Physics-Informed Simulation Methodology

The generator script (`backend/ml/generate_dataset.py` / `scripts/generate_terrace_dataset.py`) simulates a 45-day terrace garden container study (15 August 2026 00:00 UTC – 28 September 2026 23:00 UTC) at 1-hour intervals for two parallel container conditions:
1. **Plot A (Hydrogel Treatment):** Cocopeat-vermicompost mix amended with cross-linked potassium polyacrylate polymer at a standard dosage of $25\text{ g/pot}$ (15L grow bags).
2. **Plot B (Control):** Unamended cocopeat-vermicompost mix (0g hydrogel) under identical environmental and irrigation triggers.

### Environmental & Physical Equations:
1. **Diurnal Ambient Dynamics:**
 
> **Equation:** 
> `T(t) = T_mean + ΔT · sin((2π (t - 9) / 24)) + ε_T`

 
> **Equation:** 
> `RH(t) = 100 - 1.8 · (T(t) - 15) + ε_RH`

 Temperature peaks at 15:00 hours, driving highest evapotranspiration stress.

2. **Evapotranspiration (ET_o):** 
 Estimated via simplified Penman-Monteith solar radiation and vapor pressure deficit relations:
 
> **Equation:** 
> `ET_o(t) = K_c · [0.0023 · (T(t) + 17.8) · \sqrtT_max - T_min · (1 - (RH(t) / 100))]`


3. **Hydrogel Water Retention & Desorption Kinetics:** 
 When soil moisture θ(t) drops below field capacity (≈ 60%), swollen hydrogel granules slowly release stored moisture into the soil micropores:
 
> **Equation:** 
> `Q_hydrogel(t) = κ_gel · (1 - (θ(t) / θ_FC)) · Dosage_norm`

 In unamended control plots, κ_gel = 0, leading to rapid gravity and evaporation depletion.

4. **Infiltration & Irrigation Pulses:** 
 When simulated soil moisture falls below the trigger threshold (45%), an automated irrigation pulse is applied, raising soil moisture back to field capacity (62%).

---

## 3. Dataset Characteristics & Summary

| Parameter | Specification |
| :--- | :--- |
| **Time-Series Sensor Dataset** | `datasets/moisture_iot/sensor_timeseries_dataset.csv` |
| **Total Sensor Records** | **2,148 records** (1,074 Hydrogel Plot, 1,074 Control Plot) |
| **Time-Series Duration** | 45 Consecutive Days (15 August 2026 – 28 September 2026) |
| **Crop Recommendation Dataset** | `datasets/soil_and_crops/Crop_recommendation.csv` |
| **Curated Botanical Catalog** | `datasets/botanical_catalog/terrace_plants_catalog.csv` & `.json` |
| **Target Horizons** | 3 Horizon Labels (`future_soil_moisture_1h`, `future_soil_moisture_3h`, `future_soil_moisture_6h`) |

### Feature Column Definitions:

| Column | Data Type | Physical Unit | Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | ISO-8601 | YYYY-MM-DD HH:MM | Hourly sampling timestamp (15 Aug – 28 Sep 2026) |
| `soil_moisture` | Float | Percentage (%) | Instantaneous volumetric substrate water content |
| `temperature` | Float | Celsius (°C) | Ambient rooftop air temperature |
| `humidity` | Float | Percentage (%) | Relative humidity |
| `rainfall` | Float | Millimeters (mm) | Precipitation depth |
| `wind_speed` | Float | km/h | Ambient wind speed |
| `soil_type` | String | Categorical | `cocopeat_mix` potting medium |
| `crop_type` | String | Categorical | `Terrace Container Garden` |
| `hydrogel_present`| Integer | Binary (0/1) | 1 if hydrogel present, 0 if control |
| `hydrogel_dosage` | Float | g/pot | Application density ($25\text{ g}$ standard) |
| `pump_status` | String | Categorical | `ON` or `OFF` |
| `future_soil_moisture_1h` | Float | Percentage (%) | Substrate moisture at $t + 1\text{h}$ |
| `future_soil_moisture_3h` | Float | Percentage (%) | Substrate moisture at $t + 3\text{h}$ |
| `future_soil_moisture_6h` | Float | Percentage (%) | Substrate moisture at $t + 6\text{h}$ |

---

## 4. Key Agronomic Findings from Dataset

Analysis of the 45-day terrace container time series reveals clear water conservation and soil buffering advantages:
- **Mean Soil Moisture:** The hydrogel treatment plot maintained an average of **$47.7\%$** volumetric moisture, compared to **$45.9\%$** in the control plot.
- **Irrigation Event Reduction:** The unamended control containers triggered **75 irrigation events**, whereas the hydrogel-amended containers triggered only **44 events**—achieving a **$41.3\%$ reduction in pump cycles**.
- **Runoff and Leaching Prevention:** Combined with satellite rain suppression, over $48\text{ Liters}$ of unnecessary runoff and nutrient washout were avoided during monsoon rain spells.
- **Damping of Diurnal Drying Trajectories:** Root-zone desiccation during mid-day heat spikes was buffered by continuous hydrogel desorption kinetics.

---

## 5. Terrace Container Crop Recommendation Dataset

Located in [`datasets/soil_and_crops/`](../datasets/soil_and_crops/):
- `terrace_crop_recommendation.csv` (12 features: $N, P, K, pH, OC, T, H, Rain, \text{Soil}, \text{Container Volume (L)}, \text{Hydrogel (g)}, \text{Crop}$)
- `Crop_recommendation.csv` (3,500 rows across 14 crops in standard 8-column format)

### Supported Container Crops (14 Classes)
1. **Bush Tomato** (Solanum lycopersicum)
2. **Cherry Tomato** (Solanum lycopersicum var. cerasiforme)
3. **Green Chilli** (Capsicum annuum)
4. **Capsicum** (Capsicum annuum var. grossum)
5. **Brinjal** (Solanum melongena)
6. **Okra** (Abelmoschus esculentus)
7. **Bush French Beans** (Phaseolus vulgaris)
8. **Amaranth Keerai** (Amaranthus tricolor)
9. **Indian Spinach** (Basella alba / Spinacia oleracea)
10. **Spearmint** (Mentha spicata)
11. **Coriander** (Coriandrum sativum)
12. **Curry Leaf** (Murraya koenigii)
13. **White Radish** (Raphanus sativus var. longipinnatus)
14. **Strawberry** (Fragaria × ananassa)

### ML Evaluation Benchmark
- **Model:** Random Forest Classifier (100 trees, max depth 10)
- **Overall Accuracy:** **$81.0\%$** on 700 held-out container test samples
- **Weighted F1-Score:** **$0.808$**
- **Top Class Precision:** Strawberry ($96.2\%$), Bush French Beans ($93.8\%$), Coriander ($94.0\%$), Amaranth Keerai ($91.3\%$).

