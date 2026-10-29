# IRRIGATEWISE System Architecture & Engineering Blueprint

## 1. Executive Technical Overview

**IRRIGATEWISE** is an intelligent, closed-loop agricultural engineering system designed to optimize irrigation water consumption through hydrogel polymer soil amendment and predictive machine learning. 

Traditional precision irrigation architectures rely on static threshold-based rule sets (such as Soil Moisture Deficit / SMD calculation). While effective at preventing acute plant wilting, threshold mechanisms suffer from **reactive hysteresis**: irrigation is triggered only after the root zone has already depleted to critical thresholds, and cannot account for upcoming precipitation or diurnal evapotranspiration peaks. Furthermore, conventional systems do not account for the moisture buffering kinetics introduced by Superabsorbent Polymers (Hydrogel).

IRRIGATEWISE implements an end-to-end **SENSE → PREDICT → DECIDE → ACT → VERIFY** autonomous feedback control loop:

```mermaid
flowchart TD
 subgraph SENSE ["1. SENSE (Physical & Simulated Edge)"]
  S1["Capacitive Soil Moisture Sensor (v1.2)"]
  S2["DHT22 (Ambient Temp & Humidity)"]
  S3["Tipping Bucket Rain Gauge / Sensor"]
  ESP["ESP32 Microcontroller Edge Node"]
  S1 --> ESP
  S2 --> ESP
  S3 --> ESP
 end

 subgraph INGEST ["2. INGESTION & ANOMALY SCREENING"]
  API_INGEST["POST /api/v1/sensors/readings"]
  ANOMALY["Isolation Forest & Physical Sanity Filter"]
  ESP -- "JSON Telemetry over HTTP/WiFi" --> API_INGEST
  API_INGEST --> ANOMALY
  ANOMALY -- "Valid Telemetry" --> DB_RAW[("sensor_readings (PostgreSQL)")]
  ANOMALY -- "Flagged Outliers" --> DB_ANOMALY[("anomaly_events (PostgreSQL)")]
 end

 subgraph PREDICT ["3. PREDICT (Machine Learning Inference)"]
  FEAT["Feature Engineering (Lags, Rolling Means, Cyclical Encodings)"]
  GB_MODEL["Gradient Boosting Multi-Horizon Regressor (1h, 3h, 6h)"]
  DB_RAW --> FEAT
  FEAT --> GB_MODEL
  GB_MODEL --> PRED_LOG[("ml_predictions (PostgreSQL)")]
 end

 subgraph DECIDE ["4. DECIDE (Dual-Mode Decision Engine)"]
  MODE_SELECTOR"Decision Mode"
  RULE_ENGINE["Mode 1: Agronomic SMD Heuristic"]
  ML_ENGINE["Mode 2: ML Predictive + Hydrogel Offset"]
  RAIN_CHECK"Rain Forecast > 5mm?"
  DECISION["Final Irrigation Decision Matrix"]

  MODE_SELECTOR -->|Rule-Based| RULE_ENGINE
  MODE_SELECTOR -->|Autonomous ML| ML_ENGINE
  ML_ENGINE --> RAIN_CHECK
  RAIN_CHECK -->|Yes| SUPPRESS["Suppress Pump (Conserve 100% Water)"]
  RAIN_CHECK -->|No| DECISION
  RULE_ENGINE --> DECISION
 end

 subgraph ACT ["5. ACT (Pump Controller & Hardware Interlocks)"]
  CONTROLLER["Pump Controller Service"]
  SAFETY"Safety Interlocks Passed?"
  RELAY["Submersible 12V Drip Pump Relay"]
  IRR_LOG[("irrigation_events (PostgreSQL)")]

  DECISION --> CONTROLLER
  CONTROLLER --> SAFETY
  SAFETY -->|Cooldown / Moisture > 85% / Max Duration Exceeded| ABORT["Lockout / Safety Hold"]
  SAFETY -->|Clear| RELAY
  RELAY --> IRR_LOG
 end

 subgraph VERIFY ["6. VERIFY (Closed-Loop Telemetry Auditing)"]
  FEEDBACK["Ground Truth Verification (t+1h, t+3h, t+6h)"]
  EVAL["Model Drift Auditing (MAE / RMSE Tracking)"]
  IRR_LOG -.-> FEEDBACK
  DB_RAW -.-> FEEDBACK
  FEEDBACK --> EVAL
  EVAL --> FEEDBACK_LOG[("prediction_feedback (PostgreSQL)")]
 end
```

---

## 2. Multi-Tier System Topology

The IRRIGATEWISE infrastructure is organized into four decoupled tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PRESENTATION TIER (Next.js 14)                    │
│ Next.js 14 App Router • TypeScript • TailwindCSS • Framer Motion       │
│ • Executive Overview Dashboard (/dashboard)                            │
│ • Module 4: Container Plant Recommender (/recommender)                 │
│ • Modules 1 & 2: Foliar Disease & Garden Pest Diagnosis (/diagnosis)   │
│ • Module 7: Grow Bag & Container Plant Registry (/plants)              │
│ • Module 3: Potting Mix Fertility & Hydrogel Synergy Analyzer (/soil)  │
│ • Module 6: Predictive Multi-Horizon Irrigation Console (/irrigation)  │
│ • Model Success & Comparative Analytics Heatmaps (/metrics)            │
│ • Verification & Regulatory Feedback Audit (/reports)                  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTPS REST / WebSocket
┌──────────────────────────────────▼─────────────────────────────────────┐
│                       APPLICATION & API LAYER                          │
│ FastAPI (ASGI) • Pydantic v2 • SQLAlchemy 2.0 • Python 3.10+           │
│ ├── /api/v1/terrace     (Recommend, Catalog, Diagnosis, Care, Plants)  │
│ ├── /api/v1/sensors     (Telemetry Ingestion, Real-Time Cache)         │
│ ├── /api/v1/ml          (Multi-Horizon Forecasting, Crop Classifier)   │
│ ├── /api/v1/irrigation  (Dual Evaluation, Safe Pump Actuation)         │
│ ├── /api/v1/weather     (Satellite Microclimate & Rain Suppression)    │
│ ├── /api/v1/ws          (Sub-100ms WebSocket Live Telemetry Stream)   │
│ └── /api/v1/reports     (Live Analytics & Compliance CSV Exporters)    │
└──────────────┬───────────────────────────────┬─────────────────────────┘
               │                               │
┌──────────────▼───────────────┐ ┌─────────────▼─────────────────────────┐
│       INTELLIGENCE TIER      │ │            DATA PERSISTENCE           │
│ • 7-Factor Terrace Recommender│ │ PostgreSQL 16 Relational Engine       │
│ • Disease/Pest Vision Models │ │ • users                               │
│ • Feature Engineering Engine │ │ • container_plants & plant_observations│
│ • Multi-Output RF/GB Models  │ │ • soil_data & irrigation_data         │
│ • Isolation Forest Anomaly   │ │ • sensor_readings & anomaly_events    │
│ • Closed-Loop Feedback Engine│ │ • ml_predictions & prediction_feedback│
└──────────────────────────────┘ └───────────────────────────────────────┘
```

---

## 2.1 The 7 Unified Smart Terrace Gardening Modules

| Module ID | Module Title | Primary Route (UI) | API Endpoints | Core Technology & Model |
| :--- | :--- | :--- | :--- | :--- |
| **Module 1** | **Foliar Disease Screening** | `/diagnosis` | `POST /api/v1/terrace/diagnosis/disease` | MobileNetV3-Small CNN (99.77% Accuracy) on PlantVillage |
| **Module 2** | **Garden Pest Identification** | `/diagnosis` | `POST /api/v1/terrace/diagnosis/pest` | Ultralytics YOLOv8n (102 Classes) on IP102 Insect Benchmark |
| **Module 3** | **Potting Mix Health & Synergy**| `/soil` | `GET /api/v1/terrace/soil/interpretation` | Physicochemical NPK-pH Balance + WHC Calculator |
| **Module 4** | **Container Plant Recommender** | `/recommender` | `POST /api/v1/terrace/recommend`<br>`GET /api/v1/terrace/catalog` | 7-Factor Heuristic Matcher + 24-Species Catalog |
| **Module 5** | **Adaptive Care Assistant** | Dashboard widget | `POST /api/v1/terrace/care/advisory` | Micro-Irrigation Dosage Engine (mL/pot) |
| **Module 6** | **Predictive Soil Moisture** | `/irrigation` | `POST /api/v1/irrigation/predict` | Multi-Output HistGradientBoosting + Open-Meteo Weather |
| **Module 7** | **Plant Asset Registry** | `/plants` | `GET /POST /api/v1/terrace/plants`<br>`POST .../observations` | Relational Container Asset Registry & Logbook |

---

## 3. Data Flow and Ingestion Pipeline

### Step 1: Telemetry Acquisition
- Edge microcontrollers (ESP32) sample capacitive soil moisture, temperature, humidity, and rainfall every 60 seconds.
- Payloads are assembled into RFC 8259 JSON objects containing node identifier, plot type (`hydrogel` or `control`), and sensor readings.

### Step 2: Quality Filtering & Anomaly Screening
- Upon reception at `/api/v1/sensors/readings`, the payload is screened by `backend/ml/anomaly_detection.py`.
- **Physical Out-of-Bounds:** SM ∉ [5%, 95%], Temp ∉ [0°C, 60°C].
- **Spike Detection:** Sudden jumps >15% in under 5 minutes without pump actuation.
- **Freeze Detection:** Sensor values invariant over 6 hours (indicating sensor detachment or ADC failure).
- **Decoupling Detection:** Pump reported `ON` for >20 minutes without positive moisture rate of change (dSM/dt ≤ 0).

### Step 3: Feature Synthesis & Multi-Horizon Inference
- The feature pipeline computes rolling statistics (3h rolling mean, 6h rolling mean, rolling standard deviation), time lags (SM_t-1, SM_t-2, SM_t-3), cyclical diurnal features (sin(2π h/24), cos(2π h/24)), and hydrogel interaction terms.
- The pre-trained Multi-Output Regressor outputs soil moisture forecasts for t+1h, t+3h, and t+6h.

### Step 4: Closed-Loop Actuation with Physical Safety
- The decision engine evaluates if SM_3h drops below the crop management allowed depletion (MAD).
- If true, water depth requirement (mm) and volume (L) are computed, factoring in hydrogel retention efficiency.
- Safety controller verifies:
 1. Cooldown interlock (minimum 30 minutes since last pump event).
 2. Maximum runtime interlock (hard timeout at 25 minutes).
 3. Moisture saturation ceiling (immediate abort if moisture ≥ 85%).
 4. Global emergency stop switch.

### Step 5: Post-Hoc Truth Verification
- Once elapsed real time reaches t+1h, t+3h, t+6h, the system compares predicted moisture with true observed telemetry, writing records to `prediction_feedback` to dynamically track Mean Absolute Error (MAE) and model degradation.

---

## 4. Hardware and Communication Interfaces

| Component | Hardware Specification | Interface Protocol | Role in System |
| :--- | :--- | :--- | :--- |
| **Microcontroller** | ESP32-WROOM-32D Dual-Core 240MHz | Wi-Fi 802.11 b/g/n, HTTP POST | Edge telemetry collection & relay driving |
| **Soil Sensor** | Analog Capacitive Moisture Sensor v1.2 | ADC (GPIO 34, 12-bit) | Corrosion-resistant dielectric moisture sensing |
| **Ambient Sensor** | DHT22 (AM2302) | 1-Wire Digital (GPIO 4) | Air temperature & relative humidity |
| **Rain Sensor** | Optical / Conductive Digital Rain Detector | Digital Input (GPIO 18) | Precipitation detection for rain suppression |
| **Pump Actuator** | 5V Relay Module controlling 12V DC Pump | Digital Output (GPIO 23) | Closed-loop precision drip irrigation |

---

## 5. Security and Operational Integrity

1. **Authentication:** Stateless JSON Web Token (JWT) architecture using HMAC-SHA256 signatures with 24-hour expiration tokens.
2. **Password Cryptography:** High-entropy salt and password hashing via `bcrypt`.
3. **Data Protection:** Parameterized queries mediated by SQLAlchemy ORM to eradicate SQL injection vulnerabilities.
4. **Resilience & Fallback:** In the event of network disruption or ML service latency, the system automatically falls back to deterministic Rule-Based Agronomic SMD calculations to ensure zero crop desiccation risk.
