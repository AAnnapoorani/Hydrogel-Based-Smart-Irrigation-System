# Deployment & Operational Runbook

This guide covers local development, database seeding, machine learning model initialization, and operational verification for **IRRIGATEWISE v2.0**.

---

## 1. Prerequisites

- **Python:** 3.10, 3.11, or 3.12
- **Node.js:** 18 LTS or 20 LTS (with npm)
- **Database:** PostgreSQL 15/16 (or local SQLite for lightweight zero-config prototyping)
- **Git:** Standard CLI

---

## 2. Local Manual Setup (Recommended)

### Step 1: Database Setup
Ensure PostgreSQL is active locally on port 5432:
```sql
CREATE USER irrigate_user WITH PASSWORD 'irrigate_pass';
CREATE DATABASE irrigatewise OWNER irrigate_user;
```
*(Note: If PostgreSQL is not running locally, the application automatically falls back to SQLite `sqlite:///./irrigatewise.db` for instant local testing).*

---

### Step 2: Backend Setup & ML Initialization

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize deep learning model artifacts:
   ```bash
   # Downloads MobileNetV3-Small plant pathology weights and generates evaluation report
   python ml/download_plant_model.py
   ```

5. Seed database with baseline users, sensor readings, and 24 terrace container plants:
   ```bash
   # Seed core schema, user profile, and baseline sensor logs
   python seed_db.py

   # Seed curated terrace garden container plants and grow bag assets
   python seed_terrace.py
   ```

6. Start the FastAPI ASGI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

Exposed Backend Services:
- **REST API Base:** `http://localhost:8000`
- **Interactive Swagger Documentation:** `http://localhost:8000/docs`
- **ReDoc Technical Interface:** `http://localhost:8000/redoc`
- **Real-Time WebSocket Stream:** `ws://localhost:8000/api/v1/ws/telemetry`

---

### Step 3: Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Launch the Next.js development server:
   ```bash
   npm run dev
   ```

4. Access the web interface at `http://localhost:3000`.

### Active Frontend Navigation Routes:
| Route | Page Functionality |
| :--- | :--- |
| **`/dashboard`** | Executive command center with live sensor telemetry, Open-Meteo weather widget, interactive field map, and real-time connectivity status |
| **`/plants`** | Module 7: Grow Bag & Container Plant Asset Registry with health status, potting medium, and observation logs |
| **`/diagnosis`** | Modules 1 & 2: Dual foliar disease and garden pest camera diagnostic suite with treatment protocols |
| **`/recommender`** | Module 4: 7-factor terrace garden plant recommender and 24-species container catalog |
| **`/model-evaluation`** | Authoritative ML & Deep Learning performance benchmarks (ROC curves, confusion matrices, latency comparison) |
| **`/metrics`** | Multi-dimensional success analytics: 30-day water conservation impact, diurnal heatmaps, residual bell curves |
| **`/soil`** | Module 3: Potting mix physicochemical fertility analyzer and hydrogel dosage calculator |
| **`/irrigation`** | Module 6: Autonomous predictive irrigation console, pump controller, and safety interlocks |
| **`/reports`** | Regulatory compliance audit, time-series logs, and RFC 4180 CSV data exporters |

---

## 3. Running the ESP32 IoT Edge Simulator

To emulate physical ESP32 edge telemetry and stream realistic diurnal cycles directly to the server:

```bash
# Transmit 48 consecutive hourly readings at 1-second intervals
python backend/simulator/esp32_simulator.py --cycles 48 --interval 1.0

# Stream continuous infinite telemetry to local API gateway
python backend/simulator/esp32_simulator.py --url http://localhost:8000/api/v1/sensors/readings
```

Alternatively, test connectivity directly from the Web UI:
- Open the **`/dashboard`** page.
- In the top header bar, click **Simulate Packet** to generate a single diurnal packet.
- Use the **Connect / Disconnect** toggle to test edge disconnect fail-safe modes.

---

## 4. Automated Verification & Test Suite

The project includes an end-to-end automated test suite covering all machine learning regressors, deep learning vision pipelines, terrace gardening modules, decision engines, and REST endpoints:

```bash
# Run complete test suite from repository root
python -m pytest tests/ -v
```

### Expected Test Result:
```
39 passed in ~76s
```

All 39 unit and integration test cases verify:
- Multi-horizon regression inference ($t+1\text{h}$, $t+3\text{h}$, $t+6\text{h}$).
- Random Forest crop classification probabilities.
- MobileNetV3-Small plant disease inference and image validation.
- YOLOv8n insect pest taxonomy resolution and severity classification.
- Multi-criteria terrace container plant recommendation logic.
- Container soil nutrient evaluation and fertilizer adjustments.
- Hardware pump controller safety interlocks (cooldown, runtime ceiling, saturation abort).
- Sensor anomaly screening against synthetic spikes, freezes, and decoupling.
- REST API response schemas and WebSocket telemetry broadcasting.
