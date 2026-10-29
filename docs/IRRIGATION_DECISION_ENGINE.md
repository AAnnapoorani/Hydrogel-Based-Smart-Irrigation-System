# Irrigation Decision Engine, Autonomous Automation & Safety Interlocks

This document specifies the dual-mode decision architecture, the autonomous closed-loop automation engine, dynamic satellite rain suppression, container micro-irrigation dosage, and cyber-physical safety interlocks for **IRRIGATEWISE v2.0**.

---

## 1. Dual-Mode Evaluation Architecture

IRRIGATEWISE features a dual-engine architecture implemented in `backend/services/irrigation_decision_engine.py`. This enables simultaneous side-by-side computation of deterministic agronomic heuristics and autonomous predictive ML recommendations:

```
     ┌─────────────────────────────────┐
     │    Incoming Field Telemetry     │
     │ (Moisture, Temp, Hum, Rain, Oc) │
     └────────────────┬────────────────┘
                      │
     ┌────────────────┴────────────────┐
     ▼                                 ▼
  ┌───────────────────────────┐     ┌───────────────────────────┐
  │  MODE 1: RULE-BASED SMD   │     │   MODE 2: ML PREDICTIVE   │
  │ • Static Field Capacity   │     │ • Multi-Horizon Forecast  │
  │ • Instantaneous Deficit   │     │ • Hydrogel Retention Adj  │
  │ • Linear Water Volume     │     │ • Weather Rain Suppression│
  └─────────────┬─────────────┘     └─────────────┬─────────────┘
                │                                 │
                └───────────────┬─────────────────┘
                                ▼
                     ┌─────────────────────┐
                     │ Side-by-Side Matrix │
                     │ & Savings Analysis  │
                     └──────────┬──────────┘
                                ▼
                     ┌─────────────────────┐
                     │ Actuator Controller │
                     │  Safety Interlocks  │
                     └─────────────────────┘
```

---

## 2. Mode 1: Deterministic Soil Moisture Deficit (SMD)

The baseline agronomic engine computes instantaneous deficit according to FAO-56 irrigation guidelines:

$$\text{SMD} = \max(0, \theta_{\text{optimal}} - \theta_{\text{current}})$$

$$\text{Irrigation Depth (mm)} = \left(\frac{\text{SMD}}{100}\right) \times Z_r \times 1000 \times \frac{1}{\eta_{\text{sys}}}$$

$$\text{Total Water Volume (L)} = \text{Irrigation Depth (mm)} \times \text{Field Area (m}^2\text{)}$$

### Limitations of Rule-Based SMD:
1. **Reactive:** The pump fires only after root-zone moisture has already depleted into vegetative stress.
2. **Weather Blind:** It triggers watering even if a heavy thunderstorm will deliver rain 30 minutes later.
3. **Ignores Hydrogel Dynamics:** It assumes linear unamended drainage, failing to exploit the slow desorption kinetics of potassium polyacrylate polymers.

---

## 3. Mode 2: Autonomous Machine Learning Predictive Engine

Mode 2 evaluates the **forecasted root zone moisture trajectory** at $t + 3\text{h}$ ($\hat{\theta}_{3\text{h}}$) using the Histogram Gradient Boosting regressor.

### Decision Algorithm:
1. **Forecast Screening:**
   $$\text{Trigger Condition} = (\hat{\theta}_{3\text{h}} < \theta_{\text{trigger}})$$
   Where $\theta_{\text{trigger}} = 46.0\%$ for field crops (or $38.0\%$ for hydrogel terrace pots). If moisture will breach stress thresholds 3 hours ahead, replenishment is proactively scheduled.

2. **Satellite Weather Rain Suppression:**
   $$\text{Suppress Pump if } P_{\text{forecast\_24h}} \ge 2.0\text{ mm} \quad \text{or} \quad \text{Rain Probability} \ge 60\%$$
   Powered by real-time Open-Meteo satellite meteorology. When rain is imminent, the pump is suppressed, saving 100% of irrigation water.

3. **Hydrogel Retention Adjustment:**
   The required depth of water is reduced by the hydrogel water retention buffer factor:
   $$\text{Depth}_{\text{adjusted}} = \text{Depth}_{\text{standard}} \times (1 - \phi_{\text{gel}})$$
   Where $\phi_{\text{gel}} = 0.28$ (representing an empirical $28\%$ to $31\%$ reduction in applied volume due to polymer absorption efficiency).

---

## 4. The Autonomous Closed-Loop Automation Cycle (`AutomationService`)

The core innovation of IRRIGATEWISE v2.0 is the **closed-loop automation service** (`backend/services/automation_service.py`):

```
       ┌────────────────────────────────────────────────────────┐
       │   AUTONOMOUS CLOSED-LOOP PREDICTIVE CYCLE              │
       │                                                        │
       │   [1. PREDICT] ──► Forecast θ at t+1h, t+3h, t+6h      │
       │          │                                             │
       │   [2. DECIDE]  ──► Evaluate trigger + rain suppression │
       │          │                                             │
       │   [3. ACT]     ──► Dispatch pulse via safety interlock │
       │          │                                             │
       │   [4. VERIFY]  ──► Audit residual error at t+1h, t+3h  │
       └────────────────────────────────────────────────────────┘
```

### Automation Modes:
- **Telemetry-Driven:** Every valid incoming telemetry packet at `POST /api/v1/sensors/readings` triggers the evaluation cycle automatically.
- **Manual API Override:** Can be evaluated on-demand via `POST /api/v1/irrigation/automation/trigger-cycle`.
- **Configurable Flags:**
  - `autonomous_enabled`: Toggles background evaluation on/off.
  - `auto_actuation_enabled`: Toggles whether the physical relay actually fires or runs in safe decision-logging mode.
  - `simulation_mode`: Allows hardware testing without driving the physical 12V pump relay.

---

## 5. Micro-Irrigation for Terrace Containers vs. Agricultural Field

The decision engine supports both agricultural open-field hectares and urban containerized terrace gardens:

| Parameter | Field Plot (Open-Field) | Terrace Container (Potted Plants / Grow Bags) |
| :--- | :--- | :--- |
| **Units of Measurement** | Millimeters (mm) & Liters (L) | Milliliters (mL) per container pot |
| **Rooting Zone ($Z_r$)** | $0.4\text{ m}$ (400 mm) | Pot depth ($0.15\text{ m} - 0.30\text{ m}$, 5L–20L grow bags) |
| **Growing Medium** | Sandy-loam field soil | Cocopeat + Vermicompost + Perlite ($50:30:20$) |
| **Single Pulse Volume** | $1,000\text{ L} - 5,000\text{ L}$ field-wide | $200\text{ mL} - 500\text{ mL}$ per plant container |
| **Hydrogel Dosage** | $50.0\text{ g/m}^2$ broadcast application | $10\text{ g} - 25\text{ g}$ per grow bag |
| **Pump Type** | Submersible 12V agricultural pump | 12V micro-diaphragm drip pump ($200\text{ mL/min}$/emitter) |

---

## 6. Cyber-Physical Actuator Safety Interlocks (`PumpController`)

To protect hardware and prevent root-zone waterlogging, all pump activations must clear four hardware safety interlocks in `backend/services/pump_controller.py`:

```
           [ Activation Request: Volume & Duration ]
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [ Cooldown Interlock ]          [ Saturation Ceiling ]
        ≥ 30 min since last pump?       Moisture < 80% (or 85%)?
               │                               │
               └───────────────┬───────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
      [ Maximum Runtime Clamp ]       [ Emergency Stop Switch ]
       Clamped to max 10/25 min?       Global kill switch clear?
                               │
                               ▼
               [ PASS: Safe Actuation Dispatched ]
```

1. **Cooldown Lockout:** The pump cannot fire if less than **30 minutes** have elapsed since the prior cycle. Prevents rapid cycling and allows water to infiltrate down to the sensor.
2. **Moisture Saturation Ceiling:** If the physical sensor registers soil moisture $\ge 80\%$ (terrace potting mix) or $\ge 85\%$ (field soil), pump activation is immediately aborted.
3. **Maximum Runtime Clamp:** Single continuous irrigation cycles are strictly clamped to a maximum runtime (**10 minutes** for terrace containers, **25 minutes** for field drip) to prevent flooding if a network connection drops.
4. **Closed-Loop Feedback Auditing:** Every actuation event logs ground truth data to `prediction_feedback`, enabling real-time detection of model drift or sensor decay.
