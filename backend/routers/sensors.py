"""Sensors and IoT Telemetry Router for IRRIGATEWISE.

Handles:
- Ingestion of live ESP32 microcontroller packets
- Real-time sensor anomaly screening
- Sensor history for dashboard graphs
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import time

from database import get_db
import models
import schemas
# pyrefly: ignore [missing-import]
from ml.anomaly_detection import check_sensor_anomaly
from services.automation_service import AutomationService

class ESP32NodeTracker:
    """Tracks real-time connectivity and heartbeat freshness of the ESP32 IoT node."""
    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self.device_id = "ESP32_FIELD_01"
        self._last_packet_epoch: Optional[float] = None
        self._last_seen_dt: Optional[datetime] = None
        self._packets_received_session: int = 0
        self._rssi_dbm: Optional[int] = None
        self._battery_level_pct: Optional[float] = None
        self._last_reading: Optional[dict] = None
        self._manual_offline: bool = False

    def disconnect(self):
        """Explicitly forces the node into offline / disconnected state."""
        self._manual_offline = True
        self._last_packet_epoch = None

    def record_packet(
        self,
        device_id: str,
        reading_data: dict,
        rssi: Optional[int] = None,
        battery: Optional[float] = None
    ):
        self._manual_offline = False  # Reset manual offline when telemetry is received
        self.device_id = device_id or "ESP32_FIELD_01"
        self._last_packet_epoch = time.time()
        self._last_seen_dt = datetime.now(timezone.utc)
        self._packets_received_session += 1
        if reading_data:
            self._last_reading = reading_data
        if rssi is not None:
            self._rssi_dbm = rssi
        if battery is not None:
            self._battery_level_pct = battery

    def get_status(self, db: Session) -> schemas.NodeStatusOut:
        now_epoch = time.time()
        
        # If manually forced to offline mode via disconnect switch
        if self._manual_offline:
            latest_db = db.query(models.SensorReading).order_by(
                models.SensorReading.timestamp.desc()
            ).first()
            last_sm = self._last_reading.get("soil_moisture") if self._last_reading else None
            last_temp = self._last_reading.get("temperature") if self._last_reading else None
            last_hum = self._last_reading.get("humidity") if self._last_reading else None

            soil_m = float(latest_db.soil_moisture) if (latest_db and latest_db.soil_moisture is not None) else (float(last_sm) if last_sm is not None else 58.0)
            temp = float(latest_db.temperature) if (latest_db and latest_db.temperature is not None) else (float(last_temp) if last_temp is not None else 32.0)
            hum = float(latest_db.humidity) if (latest_db and latest_db.humidity is not None) else (float(last_hum) if last_hum is not None else 65.0)
            pump = str(latest_db.pump_status or "OFF") if latest_db else "OFF"
            last_dt = self._last_seen_dt or (latest_db.timestamp if latest_db else None)
            
            # pyrefly: ignore
            return schemas.NodeStatusOut(
                device_id=self.device_id,
                is_online=False,
                status="OFFLINE",
                status_label="ESP32 Offline (Disconnected)",
                last_seen=last_dt,
                seconds_since_last_reading=95.0,
                heartbeat_timeout_seconds=self.timeout_seconds,
                packets_received_session=self._packets_received_session,
                signal_strength="DISCONNECTED",
                rssi_dbm=None,
                battery_level_pct=self._battery_level_pct,
                pump_status=pump,
                soil_moisture=soil_m,
                temperature=temp,
                humidity=hum,
                message="ESP32 Node disconnected. Hardware connection in standby mode."
            )
        
        # Determine latest reading and elapsed seconds

        if self._last_packet_epoch is not None:
            seconds_ago = max(0.0, now_epoch - self._last_packet_epoch)
            is_online = seconds_ago <= self.timeout_seconds
            last_seen = self._last_seen_dt
            soil_m = self._last_reading.get("soil_moisture") if self._last_reading else None
            temp = self._last_reading.get("temperature") if self._last_reading else None
            hum = self._last_reading.get("humidity") if self._last_reading else None
            pump = self._last_reading.get("pump_status", "OFF") if self._last_reading else "OFF"
        else:
            # Check latest DB record
            latest_db = db.query(models.SensorReading).order_by(
                models.SensorReading.timestamp.desc()
            ).first()
            
            if latest_db and latest_db.timestamp:
                ts = latest_db.timestamp
                now_local = datetime.now()
                diff_local = (now_local - ts).total_seconds()
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                diff_utc = (now_utc - ts).total_seconds()
                candidates = [d for d in [diff_local, diff_utc] if d >= -5.0]
                seconds_ago = max(0.0, min(candidates)) if candidates else max(0.0, diff_local)
                
                is_online = seconds_ago <= self.timeout_seconds
                last_seen = ts
                soil_m = float(latest_db.soil_moisture) if latest_db.soil_moisture is not None else None
                temp = float(latest_db.temperature) if latest_db.temperature is not None else None
                hum = float(latest_db.humidity) if latest_db.humidity is not None else None
                pump = str(latest_db.pump_status or "OFF")
            else:
                seconds_ago = None
                is_online = False
                last_seen = None
                soil_m = None
                temp = None
                hum = None
                pump = "OFF"
        
        if is_online:
            status = "ONLINE"
            status_label = "ESP32 Live (Streaming)"
            signal = "EXCELLENT" if (self._rssi_dbm and self._rssi_dbm > -65) else "GOOD"
            sec_int = int(seconds_ago) if seconds_ago is not None else 0
            msg = f"ESP32 Node Connected & Streaming Live Telemetry (Last packet: {sec_int}s ago)"
        else:
            status = "OFFLINE"
            status_label = "ESP32 Offline (Disconnected)"
            signal = "DISCONNECTED"
            if seconds_ago is not None:
                mins = int(seconds_ago // 60)
                if mins < 1:
                    msg = f"ESP32 Disconnected. Telemetry stopped {int(seconds_ago)}s ago (timeout: {self.timeout_seconds}s)."
                elif mins < 60:
                    msg = f"ESP32 Offline. No telemetry received for {mins} minute{'s' if mins > 1 else ''}."
                else:
                    hrs = mins // 60
                    msg = f"ESP32 Offline. Last telemetry received {hrs} hour{'s' if hrs > 1 else ''} ago."
            else:
                msg = "ESP32 Disconnected. No telemetry has been received from hardware."
                
        # pyrefly: ignore
        return schemas.NodeStatusOut(
            device_id=self.device_id,
            is_online=is_online,
            status=status,
            status_label=status_label,
            last_seen=last_seen,
            seconds_since_last_reading=round(seconds_ago, 1) if seconds_ago is not None else None,
            heartbeat_timeout_seconds=self.timeout_seconds,
            packets_received_session=self._packets_received_session,
            signal_strength=signal,
            rssi_dbm=self._rssi_dbm if is_online else None,
            battery_level_pct=self._battery_level_pct,
            pump_status=pump,
            soil_moisture=soil_m,
            temperature=temp,
            humidity=hum,
            message=msg
        )

node_tracker = ESP32NodeTracker(timeout_seconds=60)

router = APIRouter(prefix="/sensors", tags=["IoT & Sensors"])

@router.post("/readings", response_model=schemas.SensorReadingOut)
def ingest_sensor_reading(
    payload: schemas.SensorReadingCreate,
    db: Session = Depends(get_db)
):
    """Ingests sensor telemetry sent by ESP32 or the simulator,

    executes ML anomaly screening, and automatically drives the autonomous
    closed-loop predictive forecasting and irrigation actuation cycle.
    """
    # 0. Record in live node tracker
    node_tracker.record_packet(
        device_id=payload.device_id or "ESP32_FIELD_01",
        reading_data={
            "soil_moisture": payload.soil_moisture,
            "temperature": payload.temperature,
            "humidity": payload.humidity,
            "pump_status": payload.pump_status or "OFF"
        }
    )

    # 1. Fetch previous reading for rate-of-change and freeze checks
    prev_reading = db.query(models.SensorReading).filter(
        models.SensorReading.device_id == payload.device_id
    ).order_by(models.SensorReading.timestamp.desc()).first()
    
    prev_m = float(prev_reading.soil_moisture) if (prev_reading and prev_reading.soil_moisture is not None) else None
    
    # Fetch recent history for freeze check
    recent_readings = db.query(models.SensorReading.soil_moisture).filter(
        models.SensorReading.device_id == payload.device_id
    ).order_by(models.SensorReading.timestamp.desc()).limit(6).all()
    recent_m = [r[0] for r in recent_readings] if recent_readings else []
    
    
    # 2. Anomaly Check
    anomaly_result = check_sensor_anomaly(
        soil_moisture=payload.soil_moisture,
        temperature=payload.temperature,
        humidity=payload.humidity,
        previous_moisture=prev_m,
        pump_status=payload.pump_status or "OFF",
        recent_history=recent_m
    )
    
    # If anomaly detected, persist in anomaly_events
    if anomaly_result["is_anomaly"]:
        anomaly_rec = models.AnomalyEvent(
            sensor_id=payload.device_id,
            anomaly_type=anomaly_result["anomaly_type"] or "sensor_fault",
            severity=anomaly_result["severity"] or "WARNING",
            value_recorded=payload.soil_moisture,
            threshold_expected="Nominal dynamic curve",
            description=anomaly_result["description"],
            resolved=0
        )
        db.add(anomaly_rec)

    # 3. Store Sensor Reading
    record = models.SensorReading(
        device_id=payload.device_id or "ESP32_FIELD_01",
        soil_moisture=payload.soil_moisture,
        temperature=payload.temperature,
        humidity=payload.humidity,
        rainfall=payload.rainfall or 0.0,
        wind_speed=payload.wind_speed or 0.0,
        soil_type=payload.soil_type or "loam",
        crop_type=payload.crop_type or "Samba Rice",
        hydrogel_present=payload.hydrogel_present if payload.hydrogel_present is not None else 1,
        hydrogel_dosage=payload.hydrogel_dosage or 50.0,
        pump_status=payload.pump_status or "OFF",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 4. Trigger Autonomous Closed-Loop ML Pipeline (PREDICT -> DECIDE -> ACT -> VERIFY)
    try:
        automation = AutomationService()
        auto_res = automation.process_sensor_telemetry(
            payload=payload,
            db=db,
            prev_reading=prev_reading,
            recent_history=recent_m
        )
        
        # Log prediction to MLPrediction table for future closed-loop feedback
        if auto_res.get("forecast"):
            f = auto_res["forecast"]
            ml_pred = models.MLPrediction(
                model_name="HistGradientBoostingRegressor",
                model_version="v1.0-production",
                current_moisture=payload.soil_moisture,
                predicted_1h=f["predicted_1h"],
                predicted_3h=f["predicted_3h"],
                predicted_6h=f["predicted_6h"],
                target_moisture=automation.target_moisture,
                irrigation_required=1 if auto_res["decision"]["irrigation_required"] else 0,
                confidence_score=f["confidence"],
                decision_mode="ml_predictive_automated",
                timestamp=datetime.now(timezone.utc)
            )
            db.add(ml_pred)
            db.commit()
    except Exception as e:
        db.rollback()
    record.is_online = True
    record.seconds_ago = 0.0

    # 5. Broadcast real-time telemetry update to WebSocket clients
    try:
        from services.websocket_manager import ws_manager
        ws_manager.broadcast_sync("TELEMETRY_UPDATE", {
            "device_id": record.device_id,
            "soil_moisture": record.soil_moisture,
            "temperature": record.temperature,
            "humidity": record.humidity,
            "rainfall": record.rainfall,
            "wind_speed": record.wind_speed,
            "pump_status": record.pump_status,
            "hydrogel_present": record.hydrogel_present,
            "hydrogel_dosage": record.hydrogel_dosage,
            "timestamp": record.timestamp.isoformat() if record.timestamp else datetime.now(timezone.utc).isoformat()
        })
        if anomaly_result.get("is_anomaly"):
            ws_manager.broadcast_sync("ANOMALY_ALERT", {
                "device_id": record.device_id,
                "anomaly_type": anomaly_result.get("anomaly_type"),
                "severity": anomaly_result.get("severity"),
                "description": anomaly_result.get("description"),
                "value_recorded": record.soil_moisture
            })
    except Exception as e:
        print(f"WebSocket broadcast error in sensors router: {e}")

    return record

@router.get("/latest", response_model=schemas.SensorReadingOut)
def get_latest_sensor_reading(db: Session = Depends(get_db)):
    """Retrieves the most recent sensor reading enriched with live connectivity status."""
    reading = db.query(models.SensorReading).order_by(models.SensorReading.timestamp.desc()).first()
    status_info = node_tracker.get_status(db)
    
    if not reading:
        # Fallback default if unseeded
        return schemas.SensorReadingOut(
            id=0,
            device_id="ESP32_FIELD_01",
            soil_moisture=58.0,
            temperature=33.5,
            humidity=68.0,
            rainfall=0.0,
            wind_speed=14.0,
            soil_type="loam",
            crop_type="Samba Rice",
            hydrogel_present=1,
            hydrogel_dosage=50.0,
            pump_status="OFF",
            timestamp=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            is_online=False,
            seconds_ago=None
        )
    
    reading.is_online = status_info.is_online
    reading.seconds_ago = status_info.seconds_since_last_reading
    return reading


@router.get("/node-status", response_model=schemas.NodeStatusOut)
def get_node_status(db: Session = Depends(get_db)):
    """Returns real-time connectivity, heartbeat status, and telemetry freshness of the ESP32 node."""
    return node_tracker.get_status(db)

@router.post("/heartbeat")
def record_esp32_heartbeat(
    payload: schemas.HeartbeatInput,
    db: Session = Depends(get_db)
):
    """Allows ESP32 microcontroller or edge daemon to send lightweight heartbeat / WiFi ping."""
    node_tracker.record_packet(
        device_id=payload.device_id or "ESP32_FIELD_01",
        reading_data={},
        rssi=payload.rssi_dbm,
        battery=payload.battery_level_pct
    )
    latest_reading = db.query(models.SensorReading).order_by(models.SensorReading.timestamp.desc()).first()
    pump_state = latest_reading.pump_status if latest_reading else "OFF"
    return {
        "status": "acknowledged",
        "device_id": payload.device_id,
        "is_online": True,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "pump_command": pump_state
    }

@router.post("/simulate-packet", response_model=schemas.SensorReadingOut)
def simulate_telemetry_packet(db: Session = Depends(get_db)):
    """One-click trigger to generate and ingest a live realistic packet for test & demonstration."""
    import random
    latest = db.query(models.SensorReading).order_by(models.SensorReading.timestamp.desc()).first()
    base_m = float(latest.soil_moisture) if (latest and latest.soil_moisture is not None) else 58.0
    new_m = max(20.0, min(80.0, round(base_m + random.uniform(-0.6, 0.4), 1)))
    temp = round(32.0 + random.uniform(-1.0, 1.5), 1)
    hum = round(64.0 + random.uniform(-2.0, 2.0), 1)
    
    mock_payload = schemas.SensorReadingCreate(
        device_id="ESP32_FIELD_01",
        soil_moisture=new_m,
        temperature=temp,
        humidity=hum,
        rainfall=0.0,
        wind_speed=14.0,
        soil_type="loam",
        crop_type="Samba Rice",
        hydrogel_present=1,
        hydrogel_dosage=50.0,
        pump_status="OFF"
    )
    return ingest_sensor_reading(payload=mock_payload, db=db)

@router.post("/disconnect", response_model=schemas.NodeStatusOut)
def disconnect_esp32_node(db: Session = Depends(get_db)):
    """Explicitly switches the ESP32 node back to offline / disconnected state."""
    node_tracker.disconnect()
    return node_tracker.get_status(db)

@router.post("/toggle-connection", response_model=schemas.NodeStatusOut)
def toggle_esp32_connection(connect: bool = True, db: Session = Depends(get_db)):
    """Toggle switch to flip between Online (simulated stream) and Offline (disconnected)."""
    if not connect:
        node_tracker.disconnect()
        return node_tracker.get_status(db)
    else:
        simulate_telemetry_packet(db=db)
        return node_tracker.get_status(db)



@router.get("/history", response_model=List[schemas.SensorReadingOut])
def get_sensor_history(limit: int = 48, db: Session = Depends(get_db)):
    """Returns recent sensor history for time-series charts."""
    readings = db.query(models.SensorReading).order_by(
        models.SensorReading.timestamp.desc()
    ).limit(limit).all()
    return readings[::-1]  # Return in chronological order

@router.get("/anomalies")
def get_sensor_anomalies(limit: int = 20, db: Session = Depends(get_db)):
    """Returns recently logged sensor and actuator anomalies."""
    anomalies = db.query(models.AnomalyEvent).order_by(
        models.AnomalyEvent.timestamp.desc()
    ).limit(limit).all()
    return anomalies
