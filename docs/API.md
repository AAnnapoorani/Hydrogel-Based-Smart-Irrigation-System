# Complete REST API Reference & WebSocket Specification

The **IRRIGATEWISE v2.0** platform exposes a high-performance, asynchronous REST and WebSocket API built with FastAPI, Pydantic v2, and SQLAlchemy. It serves enterprise IoT edge nodes, autonomous machine learning pipelines, deep learning vision models, and smart terrace gardening intelligence.

- **Base URL:** `http://localhost:8000`
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **ReDoc Specification:** `http://localhost:8000/redoc`
- **WebSocket Telemetry Stream:** `ws://localhost:8000/api/v1/ws/telemetry`

---

## 1. System Health & Legacy Endpoints

### `GET /health`
Returns backend health status, API version, and server timestamp.
- **Response `200 OK`:**
  ```json
  {
    "status": "ok",
    "service": "IrrigateWise ML & IoT Agricultural Engine",
    "version": "2.0.0",
    "timestamp": "2026-10-25T18:00:00Z"
  }
  ```

### `POST /soil/analyze` & `GET /soil/history`
Legacy soil fertility analyzer and historical testing records (NPK, pH, organic carbon).

### `POST /irrigation/calculate` & `GET /irrigation/history`
Legacy Soil Moisture Deficit (SMD) calculation and audit history.

---

## 2. IoT Sensor Ingestion & Telemetry (`/api/v1/sensors`)

### `POST /api/v1/sensors/readings`
Ingests an edge telemetry packet from an ESP32 node or the Python edge simulator. Automatically screens for sensor anomalies, updates live connectivity tracking, triggers the autonomous closed-loop ML evaluation cycle, and broadcasts real-time telemetry over WebSockets.
- **Request Body (`SensorReadingCreate`):**
  ```json
  {
    "device_id": "ESP32_FIELD_01",
    "soil_moisture": 49.2,
    "temperature": 32.1,
    "humidity": 64.0,
    "rainfall": 0.0,
    "wind_speed": 14.0,
    "soil_type": "loam",
    "crop_type": "Samba Rice",
    "hydrogel_present": 1,
    "hydrogel_dosage": 50.0,
    "pump_status": "OFF"
  }
  ```
- **Response `200 OK` (`SensorReadingOut`):** Committed sensor reading with assigned ID, UTC timestamp, online connectivity flag, and anomaly audit outcome.

### `GET /api/v1/sensors/latest`
Returns the most recent verified sensor reading enriched with connectivity status and seconds elapsed since the last packet.

### `GET /api/v1/sensors/history?limit=48`
Returns chronological time-series sensor history for chart plotting.

### `GET /api/v1/sensors/node-status`
Returns real-time hardware status, heartbeat state, RSSI signal rating (`EXCELLENT`, `GOOD`, `DISCONNECTED`), battery percentage, and packet counters.

### `POST /api/v1/sensors/heartbeat`
Lightweight heartbeat ping sent by the ESP32 microcontroller or edge daemon. Returns current pump command.

### `POST /api/v1/sensors/simulate-packet`
One-click simulation trigger generating and ingesting a realistic diurnal telemetry packet for live testing and demonstration.

### `POST /api/v1/sensors/disconnect` & `POST /api/v1/sensors/toggle-connection`
Explicitly toggles the ESP32 node between Online (streaming) and Offline (disconnected standby) states for testing fail-safe mechanisms.

### `GET /api/v1/sensors/anomalies?limit=20`
Returns recently logged sensor faults, sudden rate-of-change spikes, ADC freezes, and pump-moisture decoupling events.

---

## 3. WebSocket Real-Time Telemetry Stream (`/api/v1/ws/telemetry`)

Bidirectional WebSocket channel delivering low-latency (< 100ms) events to connected browser dashboards.
- **Connection URL:** `ws://localhost:8000/api/v1/ws/telemetry`
- **Supported Outbound Events:**
  - `TELEMETRY_UPDATE`: Broadcast whenever new sensor data is ingested.
  - `ANOMALY_ALERT`: Emitted when an anomalous spike, frozen sensor, or out-of-bounds reading is detected.
- **Client Keepalive:** Sending `"ping"` text from client responds with `{"event":"PONG"}`.

---

## 4. Machine Learning & Model Evaluation (`/api/v1/ml`)

### `POST /api/v1/ml/moisture/predict`
Executes Multi-Horizon Gradient Boosting inference for future soil moisture at $t+1\text{h}$, $t+3\text{h}$, and $t+6\text{h}$.
- **Request Body (`MoisturePredictionInput`):**
  ```json
  {
    "soil_moisture": 48.0,
    "temperature": 32.0,
    "humidity": 65.0,
    "rainfall": 0.0,
    "hour_of_day": 14,
    "hydrogel_presence": 1,
    "hydrogel_dosage": 50.0
  }
  ```
- **Response `200 OK` (`MoisturePredictionOutput`):**
  ```json
  {
    "current_moisture": 48.0,
    "predicted_1h": 46.85,
    "predicted_3h": 44.12,
    "predicted_6h": 42.90,
    "target_moisture": 62.0,
    "confidence_score": 0.88,
    "model_name": "HistGradientBoostingRegressor",
    "model_version": "v1.0-production"
  }
  ```

### `POST /api/v1/ml/crop/predict`
Predicts ranked crop recommendations with class probabilities using Random Forest (84.53% accuracy) based on N-P-K, pH, organic carbon, and climate.

### `POST /api/v1/ml/anomaly/check`
Screens an arbitrary telemetry payload against physical boundaries, rate-of-change thresholds, and historical freeze windows.

### `GET /api/v1/ml/models`
Returns active production model metadata and database-registered model versions with verified MAE, RMSE, and $R^2$ scores.

### `GET /api/v1/ml/evaluation`
Returns comparison metrics across Linear Regression, Random Forest, and Gradient Boosting.

### `GET /api/v1/ml/evaluation-details`
Returns comprehensive evaluation data including actual vs. predicted test samples (1,295 held-out records), residual distributions across horizons, and feature importance.

### `GET /api/v1/ml/dl-evaluation`
Returns authoritative Deep Learning Plant Pathology Model evaluation metrics:
- MobileNetV3-Small architecture specs (1.53M parameters).
- PlantVillage test accuracy (99.77%), precision, recall, and F1-score.
- 15-class precision/recall breakdown (Septoria, Early Blight, Late Blight, Tomato Yellow Leaf Curl, etc.).
- 15-epoch training loss and validation accuracy curves.
- Inference latency benchmark comparing MobileNetV3-Small (12ms) against ResNet-50 (54ms) and VGG-16 (122ms).

### `GET /api/v1/ml/metrics-comparison`
Returns multi-dimensional success metrics comparing ML models against non-ML methods:
- Multi-horizon regression metrics vs. naive and statistical baselines.
- $8 \times 8$ Crop Suitability Confusion Matrix.
- $2 \times 2$ Sensor Anomaly Detection Confusion Matrix & ROC statistics.
- 30-Day Operational Water Conservation & Root Stress Reduction Impact (51.2% water saved).
- 7-Day Diurnal Water Savings Heatmap Grid.
- Prediction residual error distribution with fitted Gaussian bell curve.
- 72-Hour continuous soil moisture simulation trajectory.

---

## 5. Smart Terrace Gardening Intelligence (`/api/v1/terrace`)

### `POST /api/v1/terrace/recommend`
Recommends suitable container plants for terrace gardens using a 7-factor multi-criteria constraint satisfaction algorithm.
- **Request Body (`TerraceRecommenderInput`):**
  ```json
  {
    "sunlight_hours": 6.5,
    "available_area_sqm": 8.0,
    "pot_types": ["Grow Bag 15L", "Plastic Pot 12L"],
    "growing_medium": "cocopeat_vermicompost",
    "gardener_experience": "Beginner",
    "preferred_categories": ["Vegetables", "Herbs"],
    "water_availability": "Moderate",
    "hydrogel_enabled": true
  }
  ```
- **Response `200 OK` (`TerraceRecommenderOutput`):** Ranked plant recommendations with suitability scores, recommended hydrogel dosage, watering schedule, and companion planting tips.

### `GET /api/v1/terrace/catalog`
Returns botanical details for all 24 supported terrace container species. Supports filtering by category (`Vegetables`, `Herbs`, `Flowering`, `Fruit-bearing`, `Medicinal`).

### `POST /api/v1/terrace/diagnosis/disease` (Module 1)
Analyzes an uploaded leaf photograph for foliar diseases using the MobileNetV3-Small PyTorch model.
- **Request:** `multipart/form-data` containing image `file`, optional `plant_hint`, `symptom_hint`, and `duration_days`.
- **Response `200 OK` (`PlantDiagnosisOutput`):** Disease diagnosis, confidence score, severity rating (`Mild`, `Moderate`, `Severe`), organic treatment, chemical treatment, and preventive cultural actions.

### `POST /api/v1/terrace/diagnosis/pest` (Module 2)
Analyzes an uploaded photograph for garden insect pests and feeding damage using Ultralytics YOLOv8n and the IP102 102-class entomological taxonomy.
- **Request:** `multipart/form-data` containing image `file`, optional `plant_hint`, and `symptom_hint`.
- **Response `200 OK` (`PestDiagnosisOutput`):** Detected pest name, scientific name, bounding box coordinates, pest severity, biological control (neem oil / predators), chemical pesticide recommendation, and cultural controls.

### `GET /api/v1/terrace/soil/interpretation` & `POST /api/v1/terrace/soil/evaluate` (Module 3)
Evaluates container potting mix physicochemical parameters (NPK, pH, organic carbon, moisture) against 15L container benchmarks. Returns deficit analysis, vermicompost/coco-peat adjustments, and hydrogel dosage recommendations.

### `POST /api/v1/terrace/care/advisory` (Module 5)
Synthesizes container plant biology, live sensor telemetry, growth stage, and weather forecast into daily personalized care instructions (exact watering dosage in mL/pot, sunlight adjustments, pruning, and feeding).

### `GET /api/v1/terrace/plants` & `POST /api/v1/terrace/plants` (Module 7)
Lists and registers container plants in the terrace garden asset registry. Enriched with live sensor moisture and health status.

### `DELETE /api/v1/terrace/plants/{plant_id}`
Removes a container plant from the active terrace registry.

### `GET /api/v1/terrace/plants/{plant_id}/observations` & `POST /api/v1/terrace/plants/{plant_id}/observations`
Logs and retrieves visual observations, pest sightings, and growth stage transitions for an individual container plant.

---

## 6. Predictive Irrigation & Actuation Controller (`/api/v1/irrigation`)

### `POST /api/v1/irrigation/predict`
Evaluates field telemetry across both **Mode 1 (Rule-Based SMD)** and **Mode 2 (Autonomous ML Predictive)**. Returns side-by-side comparison, water savings percentage, and rain suppression flags.

### `POST /api/v1/irrigation/execute`
Dispatches an irrigation pulse to the physical relay or hardware simulator, subject to strict safety interlocks (cooldown lockout, saturation ceiling, maximum duration).

### `GET /api/v1/irrigation/pump-status`
Returns real-time hardware actuator status (`OFF`, `ON`, `COOLDOWN`, `LOCKED`).

### `GET /api/v1/irrigation/decision-history?limit=30`
Returns audit history of past irrigation events, triggers, duration, and water volumes applied.

### `POST /api/v1/irrigation/feedback` & `GET /api/v1/irrigation/feedback`
Records and retrieves closed-loop ground-truth verification comparing predictions against observed telemetry to audit model residual error.

### `GET /api/v1/irrigation/automation/status`
Returns real-time status of the autonomous closed-loop predictive engine (`autonomous_enabled`, `auto_actuation_enabled`, `simulation_mode`, `target_moisture`).

### `POST /api/v1/irrigation/automation/toggle`
Configures autonomous closed-loop operational flags and target moisture thresholds.

### `POST /api/v1/irrigation/automation/trigger-cycle`
Manually triggers an autonomous ML evaluation and actuation cycle on the latest telemetry.

---

## 7. Live Weather & Rain Suppression (`/api/v1/weather`)

Powered by real-time Open-Meteo satellite meteorological data for Erumaiyur Village / Tambaram, Tamil Nadu (`12.9249° N, 80.1000° E`):

### `GET /api/v1/weather/current?refresh=false`
Returns live ambient temperature, relative humidity, precipitation, wind speed, solar radiation, and 24-hour rain forecast.

### `GET /api/v1/weather/forecast`
Returns 7-day meteorological forecast, hourly 12-hour projection, and precipitation trends.

### `GET /api/v1/weather/alerts`
Returns rain suppression status. If rain probability > 60% or forecasted precipitation > 2.0 mm within 24 hours, irrigation is automatically suppressed.

---

## 8. Reports & Data Export (`/api/v1/reports`)

### `GET /api/v1/reports/summary`
Returns live aggregated metrics: total soil samples, mean fertility, hydrogel water saved, and total irrigation events.

### `GET /api/v1/reports/export/soil-csv`
Downloads complete soil testing history in RFC 4180 CSV format.

### `GET /api/v1/reports/export/irrigation-csv`
Downloads complete irrigation audit history in RFC 4180 CSV format.
