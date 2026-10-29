# Machine Learning Pipeline & Soil Moisture Forecasting

This document details the mathematical formulation, feature engineering pipeline, candidate model benchmarks, deep learning architectures, and model registry for **IRRIGATEWISE v2.0**.

---

## 1. Physical Formulation: The Soil Water Balance Equation

Soil moisture dynamics in an agricultural field or terrace container amended with potassium polyacrylate hydrogel polymers can be modeled physically as a continuous mass-balance differential equation:

$$\frac{\partial\theta}{\partial t} = -\frac{\text{ET}_o(\text{Temp}, \text{Hum}, \text{Rad})}{Z_r} + \frac{P + I}{Z_r} + Q_{\text{gel}}(\theta, D_{\text{gel}}) - D_r(\theta)$$

### The "Soil Water Bank Account" Analogy:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                       SOIL WATER BALANCE BANK ACCOUNT                         │
│                                                                               │
│  [New Moisture] = [Old Moisture] - [Evaporation Loss] + [Water Influx]        │
│                         + [Hydrogel Released] - [Drainage Leak]               │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Discrete Hourly Form (As Computed in Code):

$$\theta_{t+1} = \theta_t - \Delta\theta_{\text{evap}} + \Delta\theta_{\text{rain}} + \Delta\theta_{\text{irrigation}} + \Delta\theta_{\text{hydrogel}} - \Delta\theta_{\text{drainage}}$$

### Component-by-Component Formula Breakdown:

| Mathematical Term | Parameter Name | Physical Meaning | Practical Code Implementation |
| :--- | :--- | :--- | :--- |
| **$\frac{\partial\theta}{\partial t}$** | **Rate of Change** | How fast soil is drying ($-$) or wetting ($+$) (%/hour) | `moisture_rate_of_change = sm - prev_sm` |
| **$-\frac{\text{ET}_o}{Z_r}$** | **Evapotranspiration** | Water lost to solar heating, dry air, and plant transpiration | `hourly_loss = et0 * et_mult * et_retention * 0.45` |
| **$+\frac{P + I}{Z_r}$** | **Moisture Influx** | Water added to soil via rainfall ($P$) or pump pulse ($I$) | `sm += rainfall * 0.85 + irrigation * 1.5` |
| **$+Q_{\text{gel}}$** | **Hydrogel Desorption** | Swollen polymer micro-beads slowly releasing water to roots | `et_retention = 1.0 / (1.0 + 0.015 * dosage)` |
| **$-D_r(\theta)$** | **Deep Drainage** | Gravitational percolation lost when soil exceeds Field Capacity | `drain_loss = excess * drain_rate * drain_damping` |

---

## 2. Multi-Horizon Soil Moisture Regression

Rather than predicting instantaneous moisture (which is already measured at $t = 0$ by the capacitive probe), the machine learning task is to forecast future trajectory at three operational horizons:

1. **$t + 1\text{h}$ Horizon:** Real-time infiltration verification and sensor drift filtering.
2. **$t + 3\text{h}$ Horizon:** Primary operational decision window (triggering pump before root zone reaches critical wilting).
3. **$t + 6\text{h}$ Horizon:** Diurnal planning horizon (identifying whether midday sun or night cooling will alter drying).

$$\hat{\mathbf{Y}}_t = \left[\hat{\theta}_{t+1\text{h}}, \hat{\theta}_{t+3\text{h}}, \hat{\theta}_{t+6\text{h}}\right] = f_{\Theta}(\mathbf{X}_t)$$

### Engineered Feature Pipeline (`backend/ml/feature_engineering.py`):
```
Raw Telemetry (t) ──► [ Lag Generator ] ──────► θ(t-1), θ(t-2), θ(t-3)
                  ──► [ Rolling Windows ] ────► Mean_3h, Mean_6h, Std_3h, Std_6h
                  ──► [ Cyclical Encoders ] ──► sin(2π h/24), cos(2π h/24)
                  ──► [ Physical Interactions]► Hydrogel * Temp, Evap_Stress_Index
```

1. **Autoregressive Lags:** `moisture_lag_1`, `moisture_lag_2`, `moisture_lag_3` capture recent drying trajectory.
2. **Rolling Statistics:** `moisture_rolling_mean_3h`, `moisture_rolling_mean_6h`, `moisture_rolling_std_3h` smooth high-frequency ADC noise.
3. **Rate of Change & Evaporative Stress:**
   $$\text{evap\_stress\_index} = \text{Temperature} \times \left(1 - \frac{\text{Humidity}}{100}\right)$$
4. **Diurnal Cyclical Encoders:**
   $$\text{hour\_sin} = \sin\left(\frac{2\pi \cdot \text{hour}}{24}\right), \quad \text{hour\_cos} = \cos\left(\frac{2\pi \cdot \text{hour}}{24}\right)$$
   Smoothly maps solar radiation peaks without artificial discontinuity between 23:00 and 00:00.
5. **Hydrogel Interaction Terms:** `hydrogel_present`, `hydrogel_dosage`, and `hours_since_irrigation`.

### Model Evaluation on Unseen Test Split ($N = 1,295$):
- **HistGradientBoostingRegressor (Production):**
  - **Overall Test MAE:** **1.197%**
  - **Overall Test RMSE:** **2.572%**
  - **Overall Test $R^2$:** **0.7312**
  - Horizon $t+1\text{h}$: $\text{MAE} = 0.472\%, R^2 = 0.9479$
  - Horizon $t+3\text{h}$: $\text{MAE} = 1.198\%, R^2 = 0.7269$
  - Horizon $t+6\text{h}$: $\text{MAE} = 1.921\%, R^2 = 0.5187$

---

## 3. Crop Suitability Recommender (`CropRecommender`)

A multi-class **Random Forest Classifier** trained on 3,200 agronomic soil profiles across 8 crops (`Samba Rice`, `Sugarcane`, `Cotton`, `Groundnut`, `Maize`, `Finger Millet`, `Black Gram`, `Green Gram`):
- **Test Accuracy:** **84.53%**
- **Macro F1-Score:** **0.8451**
- **Inputs:** Nitrogen, Phosphorus, Potassium, pH, Organic Carbon, Temperature, Humidity, Rainfall, Soil Type.
- **Output:** Ranked candidate crops with class prediction probabilities and tailored hydrogel dosage advice.

---

## 4. Deep Learning Foliar Pathology Classifier (`PlantDiseaseClassifier`)

A lightweight convolutional neural network optimized for edge diagnosis:
- **Base Architecture:** **MobileNetV3-Small** (PyTorch) with Hard-Swish activations and Squeeze-and-Excitation residual blocks.
- **Model Footprint:** **1.53M parameters** (6.1 MB file size), enabling sub-15ms CPU inference.
- **Benchmark:** PlantVillage dataset across 15 foliar disease and healthy categories (Tomato, Potato, Pepper).
- **Test Accuracy:** **99.77%** (Macro Precision 0.998, Macro Recall 0.997, Macro F1 0.997).
- **Clinical Outputs:** Pathogen identification, severity grading, organic treatment (neem/copper soap), chemical fungicides, and preventive cultural actions.

---

## 5. Garden Pest Object Detector (`YOLOPestDetector`)

Computer vision insect detection using **Ultralytics YOLOv8n**:
- **Taxonomy:** IP102 Large-Scale Insect Pest ontology (102 agricultural and garden pest classes).
- **mAP@50:** **0.784** with 28ms CPU inference.
- **Output:** Bounding box spatial coordinates, identified pest species, severity rating, and dual biological/chemical Integrated Pest Management (IPM) protocols.

---

## 6. Multi-Criteria Terrace Garden Recommender

A constraint-satisfaction heuristic engine (`TerraceRecommenderService`) that evaluates container garden parameters against a curated 24-species botanical catalog:
- **Constraint Factors:** Daily sunlight hours, container volume (5L–25L), growing medium, gardener skill, water availability, and hydrogel status.
- **Catalog Coverage:** Potted vegetables, culinary herbs, flowering pollinator plants, fruit-bearing dwarfs, and medicinal species.

---

## 7. Model Registry & Version Control (`ModelRegistry`)

All models and hyperparameter metadata are managed through `backend/ml/model_registry.py` and synchronized with the PostgreSQL `ml_model_versions` table:
```sql
SELECT id, model_name, version_tag, mae, rmse, r2_score, is_active, trained_at
FROM ml_model_versions;
```
Candidate model versions undergo automated validation on held-out splits before flipping the `is_active` flag, guaranteeing atomic, zero-downtime model deployments.
