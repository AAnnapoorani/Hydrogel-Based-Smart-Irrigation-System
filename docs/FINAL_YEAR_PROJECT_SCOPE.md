# Academic Scope, CSE Thesis Mapping & Project Defense Guide

This document details the final-year Computer Science & Engineering (CSE) capstone competencies, curriculum mappings, United Nations SDG alignments, and academic viva defense preparation for **IRRIGATEWISE v2.0**.

---

## 1. Final-Year CSE Capstone Competencies

**IRRIGATEWISE** satisfies all major curriculum outcomes for an undergraduate CSE capstone project by integrating six core computing domains into a unified, cyber-physical engineering artifact:

```
                      ┌─────────────────────────────────────────┐
                      │        IRRIGATEWISE CSE CAPSTONE        │
                      └────────────────────┬────────────────────┘
                                           │
         ┌──────────────────┬──────────────┼──────────────┬──────────────────┐
         ▼                  ▼              ▼              ▼                  ▼
┌─────────────────┐ ┌───────────────┐ ┌──────────┐ ┌─────────────┐ ┌─────────────────┐
│ Machine Learning│ │  Internet of  │ │Distributed│ │ Closed-Loop │ │ Human-Computer  │
│ & Deep Learning │ │  Things Edge  │ │ Systems  │ │  Control &  │ │Interaction (HCI)│
│                 │ │               │ │          │ │   Safety    │ │                 │
│ • Multi-Horizon │ │ • ESP32 Node  │ │ • FastAPI│ │ • Sense-    │ │ • Next.js 14    │
│   Regression    │ │ • 60s Timeout │ │ • Postgre-│   Predict-   │   App Router      │
│ • MobileNetV3   │ │ • Telemetry   │ │   SQL 16 │   Decide-     │ • WebSockets      │
│   Vision (CNN)  │ │   Tracking    │ │ • Pydantic│   Act-Verify  │ • Dynamic Charts  │
│ • YOLOv8n Pest  │ │ • WebSocket   │ │   v2     │ • Safety      │ • Responsive UI   │
│ • Random Forest │ │ • Simulator   │ │ • Docker │   Interlocks  │ • Dark/Light Mode │
└─────────────────┘ └───────────────┘ └──────────┘ └─────────────┘ └─────────────────┘
```

---

## 2. Curriculum Competency Matrix

| CSE Knowledge Domain | Implemented Artifacts in IrrigateWise | Source Directory |
| :--- | :--- | :--- |
| **Applied Machine Learning & Vision** | • Multi-Output HistGradientBoosting Regressor ($t+1\text{h}, t+3\text{h}, t+6\text{h}$)<br>• Random Forest Crop Suitability Classifier (84.53% Accuracy)<br>• MobileNetV3-Small Deep Learning Plant Pathology CNN (99.77% Accuracy)<br>• Ultralytics YOLOv8n Pest Detector with IP102 102-Class Taxonomy<br>• 7-Factor Terrace Garden Constraint Satisfaction Recommender | `backend/ml/`<br>`backend/services/` |
| **Embedded & IoT Systems** | • ESP32 Microcontroller firmware architecture & GPIO pinout<br>• Real-time `ESP32NodeTracker` with 60-second heartbeat timeout<br>• Bidirectional sub-100ms WebSocket telemetry streaming (`/api/v1/ws/telemetry`)<br>• Realistic diurnal edge telemetry simulator CLI with fault injection | `backend/routers/sensors.py`<br>`backend/simulator/`<br>`backend/services/websocket_manager.py` |
| **Cyber-Physical Safety Engineering** | • Multi-condition anomaly screening (range sanity, spikes, ADC freeze, decoupling)<br>• 4-Tier pump safety interlocks (cooldown lockout, saturation abort, runtime clamp)<br>• Closed-loop ground truth feedback tracking (`prediction_feedback`) | `backend/services/pump_controller.py`<br>`backend/services/automation_service.py`<br>`backend/ml/anomaly_detection.py` |
| **Backend Architecture & APIs** | • High-throughput asynchronous FastAPI ASGI microservice<br>• PostgreSQL relational schema (10 tables, strict foreign keys, indexing)<br>• Pydantic v2 type validation and OpenAPI/Swagger documentation | `backend/`<br>`backend/models.py`<br>`backend/schemas.py` |
| **Modern Frontend Engineering** | • Next.js 14 App Router with React Server Components & TypeScript<br>• 9 comprehensive interactive pages (`/dashboard`, `/plants`, `/diagnosis`, `/recommender`, `/model-evaluation`, `/metrics`, `/soil`, `/irrigation`, `/reports`)<br>• Recharts multi-axis visualization and Framer Motion micro-animations | `frontend/src/app/`<br>`frontend/src/components/` |
| **Software Verification & Quality** | • 39 automated unit, integration, and ML inference test cases (`pytest`)<br>• End-to-end regression validation and anomaly detection benchmarking | `tests/` |

---

## 3. United Nations Sustainable Development Goals (SDG) Alignment

1. **SDG 6: Clean Water and Sanitation (Target 6.4)**
   - *Target:* Substantially increase water-use efficiency across all sectors and ensure sustainable withdrawals.
   - *IrrigateWise Impact:* Demonstrates a **51.2% total water savings** vs. traditional timer irrigation and **30.9% reduction** vs. reactive SMD through predictive hydrogel buffering and satellite rain suppression.
2. **SDG 11: Sustainable Cities and Communities (Target 11.7)**
   - *Target:* Strengthen green urban spaces and sustainable urban food systems.
   - *IrrigateWise Impact:* Empowers urban citizens to cultivate resilient terrace gardens, potted vegetables, and micro-crops using container micro-irrigation and disease diagnosis.
3. **SDG 12: Responsible Consumption and Production (Target 12.2)**
   - *Target:* Achieve sustainable management and efficient use of natural resources.
   - *IrrigateWise Impact:* Eliminates over-irrigation runoff, fertilizer leaching into urban stormwater drains, and unnecessary chemical pesticide applications via IPM pest identification.
4. **SDG 13: Climate Action (Target 13.1)**
   - *Target:* Strengthen resilience and adaptive capacity to climate-related hazards and natural disasters.
   - *IrrigateWise Impact:* Shields crops and container plants against intense tropical heatwaves through hydrogel moisture desorption.

---

## 4. Academic Defense & Viva Q&A Cheat Sheet

### Q1: Why use Machine Learning for soil moisture when you already have physical sensors?
> **Answer:** "Physical capacitive sensors provide only **instantaneous reactive feedback** ($t = 0$). By the time a sensor detects that moisture has fallen below the critical threshold, crop roots have already entered vegetative stress. Furthermore, simple sensors cannot anticipate upcoming weather or diurnal solar peaks. Our Gradient Boosting regressor predicts **future moisture trajectories at $t+1\text{h}$, $t+3\text{h}$, and $t+6\text{h}$**, enabling proactive irrigation dispatch and allowing upcoming rainfall to suppress redundant pump events."

### Q2: Why did Gradient Boosting outperform Linear Regression and Random Forest?
> **Answer:** "Soil moisture depletion is governed by non-linear physical differential equations involving exponential evaporation, vapor pressure deficits, and non-linear hydrogel desorption. Linear Regression was insufficient ($R^2 = 0.3345$). While Random Forest achieved strong performance ($R^2 = 0.7013$), Gradient Boosting sequentially minimizes residual loss across multiple output horizons, achieving the lowest test error (MAE $= 1.197\%$, RMSE $= 2.572\%$, $R^2 = 0.7312$)."

### Q3: Why did you choose MobileNetV3-Small over larger architectures like ResNet-50 or VGG-16 for plant disease diagnosis?
> **Answer:** "In an IoT and edge agricultural setting, computational efficiency, disk footprint, and inference latency are critical constraints. ResNet-50 has 25.6M parameters and VGG-16 has 138.4M parameters, requiring heavy GPU hardware. MobileNetV3-Small achieves **99.77% test accuracy** on the PlantVillage benchmark with only **1.53M parameters** and an inference latency of **12.4ms on standard CPU**. This makes it feasible to run directly on edge micro-gateways like the Raspberry Pi or via fast mobile uploads."

### Q4: How does the system handle an edge sensor disconnect or packet dropout?
> **Answer:** "We built an active `ESP32NodeTracker` with a 60-second heartbeat timeout. If the node fails to transmit within 60 seconds, status transitions to `OFFLINE`. When disconnected, the system holds the pump in safe standby mode (preventing unmonitored flooding), retains the last verified reading with an elapsed time counter, and broadcasts a connectivity alert to the UI via WebSockets."

### Q5: What prevents the autonomous system from flooding the field if the ML model hallucinates or drifts?
> **Answer:** "We implemented strict **defense-in-depth safety interlocks** in `backend/services/pump_controller.py`. Even if the ML model commands irrigation, the actuator will reject the command if:
> 1. Less than 30 minutes has elapsed since the last cycle (Cooldown lockout).
> 2. The physical sensor indicates soil moisture is $\ge 80\%$ (Saturation ceiling).
> 3. The requested duration exceeds the hard safety limit (Clamped to maximum 10 or 25 minutes).
> 4. Incoming rainfall is detected $\ge 2.0\text{ mm}$ or rain probability $\ge 60\%$ (Weather override)."

### Q6: What is the proposed Future Scope of this project?
> **Answer:** "The primary planned extensions are:
> 1. **Cyber-Physical 3D Subsurface Digital Twin:** Modeling non-linear Richards' unsaturated flow equations coupled with hydrogel swelling in 3D voxel space to simulate drought stress and isolate pipe leaks.
> 2. **Drone (UAV) Multispectral Calibration:** Using aerial NDVI/NDWI imagery to calibrate crop coefficients ($K_c$) across micro-plots.
> 3. **Long-Range LoRaWAN Mesh Networking:** Replacing direct Wi-Fi links with ultra-low-power LoRaWAN gateways for rural farm deployment."
