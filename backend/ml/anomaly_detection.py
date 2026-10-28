"""Sensor and Actuation Anomaly Detection Engine for IRRIGATEWISE.

Combines statistical Isolation Forest modeling with domain physiological
boundary checks to identify sensor faults, impossible jumps, freezing, and
pump-irrigation decoupling.
"""

import os
# pyrefly: ignore [missing-import]
import joblib
# pyrefly: ignore [missing-import]
import numpy as np
from typing import Dict, Any, Optional, List, cast
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sklearn.ensemble import IsolationForest

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "anomaly_model.joblib")

class AnomalyDetector:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnomalyDetector, cls).__new__(cls)
            cls._instance._init_model()
        return cls._instance
        
    def _init_model(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            # Fit Isolation Forest on standard baseline distribution
            np.random.seed(42)
            normal_moisture = np.random.normal(55, 12, 1000)
            normal_temp = np.random.normal(31, 4, 1000)
            normal_hum = np.random.normal(68, 10, 1000)
            X_normal = np.column_stack([normal_moisture, normal_temp, normal_hum])
            
            self.model = IsolationForest(
                n_estimators=100,
                contamination=cast(Any, 0.03),
                random_state=42
            )
            self.model.fit(cast(Any, X_normal))
            joblib.dump(self.model, MODEL_PATH)

    def check_telemetry(
        self,
        soil_moisture: float,
        temperature: float,
        humidity: float,
        previous_moisture: Optional[float] = None,
        pump_status: str = "OFF",
        recent_history: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Runs multi-tiered anomaly validation:

        Tier 1: Physical / Physiological bounds (Hard limits)
        Tier 2: Rate of change / Spike detection
        Tier 3: Sensor freeze / Dead sensor detection
        Tier 4: Actuation decoupling (Pump ON, zero moisture delta)
        Tier 5: Multivariate Isolation Forest density check
        """
        # Tier 1: Physical Boundary Checks
        if soil_moisture < 0.0 or soil_moisture > 100.0:
            return {
                "is_anomaly": True,
                "status": "ANOMALY",
                "anomaly_type": "impossible_moisture_value",
                "severity": "CRITICAL",
                "description": f"Physically impossible soil moisture reading: {soil_moisture}%. Sensor range is [0.0%, 100.0%]."
            }
            
        if temperature < 2.0 or temperature > 55.0:
            return {
                "is_anomaly": True,
                "status": "ANOMALY",
                "anomaly_type": "extreme_temperature",
                "severity": "CRITICAL",
                "description": f"Abnormal ambient temperature: {temperature}°C exceeds agro-climatic boundaries for Tamil Nadu."
            }
            
        if humidity < 5.0 or humidity > 100.0:
            return {
                "is_anomaly": True,
                "status": "ANOMALY",
                "anomaly_type": "impossible_humidity",
                "severity": "WARNING",
                "description": f"Relative humidity {humidity}% out of physical atmospheric boundaries."
            }
            
        # Tier 2: Sudden Spike / Jolt Detection
        if previous_moisture is not None:
            delta = abs(soil_moisture - previous_moisture)
            # A 25% instantaneous jump without a pump pulse is physically abnormal in dense soil
            if delta > 25.0 and pump_status != "ON":
                return {
                    "is_anomaly": True,
                    "status": "ANOMALY",
                    "anomaly_type": "sudden_spike",
                    "severity": "WARNING",
                    "description": f"Abnormal moisture jump: shifted by {delta:.1f}% ({previous_moisture}% -> {soil_moisture}%) in a single cycle without active irrigation."
                }

        # Tier 3: Sensor Freeze Detection
        if recent_history and len(recent_history) >= 6:
            # If standard deviation over last 6 readings is effectively zero
            if float(np.std(recent_history)) < 0.001:
                return {
                    "is_anomaly": True,
                    "status": "ANOMALY",
                    "anomaly_type": "sensor_freeze",
                    "severity": "WARNING",
                    "description": f"Sensor values have flatlined identically ({recent_history[0]}%) over multiple cycles. Suspected hardware freeze or ADC lockup."
                }

        # Tier 4: Actuator Decoupling Check (Pump ON, zero response)
        if pump_status == "ON" and previous_moisture is not None:
            if soil_moisture <= previous_moisture:
                return {
                    "is_anomaly": True,
                    "status": "ANOMALY",
                    "anomaly_type": "pump_no_response",
                    "severity": "CRITICAL",
                    "description": "Irrigation pump is engaged ON, but no corresponding increase in root-zone soil moisture was detected. Check pump power, pipe blockages, or solenoid valve."
                }

        # Tier 5: Multivariate Statistical Outlier
        X = np.array([[soil_moisture, temperature, humidity]])
        score = self.model.predict(cast(Any, X))[0]  # -1 = anomaly, 1 = normal
        if score == -1:
            return {
                "is_anomaly": True,
                "status": "ANOMALY",
                "anomaly_type": "multivariate_statistical_outlier",
                "severity": "INFO",
                "description": f"Unusual environmental combination detected by Isolation Forest (Moisture: {soil_moisture}%, Temp: {temperature}°C, Hum: {humidity}%)."
            }

        return {
            "is_anomaly": False,
            "status": "NORMAL",
            "anomaly_type": None,
            "severity": None,
            "description": "All sensor parameters are within nominal physical and statistical operating ranges."
        }

def check_sensor_anomaly(
    soil_moisture: float,
    temperature: float,
    humidity: float,
    previous_moisture: Optional[float] = None,
    pump_status: str = "OFF",
    recent_history: Optional[List[float]] = None
) -> Dict[str, Any]:
    detector = AnomalyDetector()
    return detector.check_telemetry(
        soil_moisture=soil_moisture,
        temperature=temperature,
        humidity=humidity,
        previous_moisture=previous_moisture,
        pump_status=pump_status,
        recent_history=recent_history
    )
