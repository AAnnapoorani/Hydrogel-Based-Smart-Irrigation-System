# IoT Edge Architecture & ESP32 Integration

This document specifies the embedded hardware topology, edge-to-cloud communication protocols, connectivity tracking, and anomaly screening for **IRRIGATEWISE v2.0**.

---

## 1. Microcontroller Hardware Topology

IRRIGATEWISE edge nodes utilize the **ESP32-WROOM-32D** dual-core microcontroller (Tensilica Xtensa 32-bit LX6, 240 MHz, 520 KB SRAM, integrated 2.4 GHz Wi-Fi radio). It supports both rural agricultural field plots and urban terrace garden container installations.

```
 ┌────────────────────────────────────────────────────────┐
 │                ESP32 Microcontroller                   │
 │                                                        │
 │ [GPIO 34 / ADC1_CH6] ◄── Analog Capacitive Moisture    │
 │ [GPIO 4 / 1-Wire]    ◄── DHT22 (Temp & Relative Hum)   │
 │ [GPIO 18 / Digital]  ◄── Rain Detection Sensor         │
 │ [GPIO 23 / Output]   ──► 5V Relay Module (12V Pump)    │
 │ [2.4 GHz Wi-Fi]      ──► HTTP REST & WebSocket Gateway │
 └────────────────────────────────────────────────────────┘
```

### Sensor Hardware Pinout & Electrical Characteristics:

| Component | Sensor Pin | ESP32 Pin | Logic Level | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Capacitive Soil Sensor (v1.2)** | VCC | 3.3V | DC | Avoids electrolysis corrosion seen in resistive probes |
| | GND | GND | Ground | Common reference ground |
| | AOUT | GPIO 34 | 0–3.3V Analog | 12-bit ADC reading ($0 = \text{Air}$, $4095 = \text{Water}$) |
| **DHT22 Temperature & Humidity** | VCC | 3.3V | DC | Digital 1-wire communication |
| | DATA | GPIO 4 | 3.3V Logic | 10k $\Omega$ pull-up resistor |
| | GND | GND | Ground | Common reference ground |
| **Rain Detection Sensor** | DOUT | GPIO 18 | 3.3V Logic | Active Low (LOW indicates precipitation) |
| **12V Micro-Drip Pump Relay** | IN | GPIO 23 | 3.3V Logic | Active High driving optocoupler galvanic isolation |

---

## 2. Telemetry Packet Schema

Edge devices serialize telemetry into standard JSON packets transmitted via HTTP `POST /api/v1/sensors/readings`:

```json
{
  "device_id": "ESP32_FIELD_01",
  "soil_moisture": 48.65,
  "temperature": 31.4,
  "humidity": 68.2,
  "rainfall": 0.0,
  "wind_speed": 14.0,
  "soil_type": "loam",
  "crop_type": "Samba Rice",
  "hydrogel_present": 1,
  "hydrogel_dosage": 50.0,
  "pump_status": "OFF",
  "timestamp": "2026-10-25T11:30:00Z"
}
```

---

## 3. Real-Time Hardware Connectivity & Heartbeat Tracker

To ensure resilience against network dropouts and hardware power failures, the backend implements an active node tracking service (`ESP32NodeTracker` in `backend/routers/sensors.py`):

### Operational Rules:
1. **Heartbeat Timeout Window:** Configured to **60 seconds**. If no telemetry packet or lightweight heartbeat is received within 60 seconds, the node status transitions automatically to `OFFLINE`.
2. **Signal Strength Classification:**
   - $\text{RSSI} > -65\text{ dBm}$: `EXCELLENT` signal.
   - $-85\text{ dBm} \le \text{RSSI} \le -65\text{ dBm}$: `GOOD` signal.
   - Node timeout or disconnected: `DISCONNECTED`.
3. **Fail-Safe Behavior:** When disconnected, the system:
   - Holds the pump in safe `OFF` mode (preventing unmonitored flooding).
   - Retains the last valid sensor reading with an explicit elapsed seconds counter.
   - Broadcasts a connectivity alert over WebSockets.
4. **Heartbeat Endpoint:** ESP32 nodes can send periodic low-overhead ping packets via `POST /api/v1/sensors/heartbeat` containing `rssi_dbm` and `battery_level_pct` without transmitting full sensor data.

---

## 4. WebSocket Low-Latency Streaming (`/api/v1/ws/telemetry`)

The platform provides a native WebSocket server (`services/websocket_manager.py`) delivering sub-100ms updates directly to connected browser clients:

- **Endpoint:** `ws://localhost:8000/api/v1/ws/telemetry`
- **Events Broadcast:**
  - `TELEMETRY_UPDATE`: Emitted synchronously upon receiving and verifying any edge packet.
  - `ANOMALY_ALERT`: Emitted immediately when physical out-of-bounds, sudden spikes, or frozen readings are detected.

---

## 5. Python ESP32 Edge Simulator CLI

To enable rigorous testing and continuous integration without physical microcontrollers attached, the platform includes a feature-complete edge simulator (`backend/simulator/esp32_simulator.py`).

### Key Simulator Features:
1. **Diurnal Cycle Modeling:** Simulates realistic solar heating curves (temperature peak at 15:00, humidity depression, diurnal evapotranspiration).
2. **Dual-Plot Generation:** Emulates both hydrogel-amended soil (slow moisture desorption) and unamended control soil (rapid drying).
3. **Dynamic Infiltration Response:** When pump status transitions to `ON`, subsequent cycles simulate moisture infiltration rising back to field capacity (62%).
4. **Fault Injection Mode:** Can inject synthetic sensor spikes, frozen ADC values, or pump-relay decoupling to test anomaly detection algorithms.

### Running the Simulator:
```bash
# Transmit 48 continuous hourly cycles at 1-second intervals
python backend/simulator/esp32_simulator.py --cycles 48 --interval 1.0

# Stream continuous infinite telemetry to local API gateway
python backend/simulator/esp32_simulator.py --url http://localhost:8000/api/v1/sensors/readings
```

---

## 6. Anomaly Screening Pipeline

Ingested telemetry packets are screened by `backend/ml/anomaly_detection.py` prior to database insertion:

1. **Physical Range Sanity:**
   $$\theta \in [5.0\%, 95.0\%] \quad \text{and} \quad T \in [0.0^\circ\text{C}, 60.0^\circ\text{C}]$$
   Catches detached probes or power rail brownouts.

2. **Instantaneous Spike Filter:**
   $$|\theta(t) - \theta(t-1)| > 15.0\% \quad \text{with Pump OFF} \implies \text{Outlier Spike}$$
   Filters electrical noise, loose jumper wires, or water splashes on probe circuitry.

3. **ADC Freeze Detection:**
   $$\sigma(\theta_{t-6:t}) = 0.0 \implies \text{Frozen ADC / Sensor Detached}$$
   Detects microcontrollers whose analog-to-digital converter has crashed or locked up.

4. **Pump-Moisture Decoupling:**
   $$\text{Pump ON for } > 20\text{ min} \quad \text{and} \quad \Delta\theta \le 0 \implies \text{Pump Air-Lock / Pipe Rupture}$$
   Prevents catastrophic motor burn-out and flooding by cutting power if soil moisture fails to respond to pumping.
