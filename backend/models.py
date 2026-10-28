# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from database import Base
from typing import Any


class User(Base):
    __tablename__ = "users"
    id: Any = Column(Integer, primary_key=True, index=True)
    name: Any = Column(String, nullable=False)
    email: Any = Column(String, unique=True, nullable=False, index=True)
    password: Any = Column(String, nullable=False)
    created_at: Any = Column(DateTime, server_default=func.now())

    soil_records = relationship("SoilData", back_populates="user")
    irrigation_records = relationship("IrrigationData", back_populates="user")
    irrigation_events = relationship("IrrigationEvent", back_populates="user")


class SoilData(Base):
    __tablename__ = "soil_data"
    id: Any = Column(Integer, primary_key=True, index=True)
    user_id: Any = Column(Integer, ForeignKey("users.id"), nullable=False)
    nitrogen: Any = Column(Float, nullable=False)
    phosphorus: Any = Column(Float, nullable=False)
    potassium: Any = Column(Float, nullable=False)
    ph: Any = Column(Float, nullable=False)
    organic_carbon: Any = Column(Float, nullable=False)
    fertility_score: Any = Column(Float, nullable=False)
    classification: Any = Column(String, nullable=False)
    created_at: Any = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="soil_records")


class IrrigationData(Base):
    __tablename__ = "irrigation_data"
    id: Any = Column(Integer, primary_key=True, index=True)
    user_id: Any = Column(Integer, ForeignKey("users.id"), nullable=False)
    sm_current: Any = Column(Float, nullable=False)
    sm_optimal: Any = Column(Float, nullable=False)
    smd: Any = Column(Float, nullable=False)
    irrigation_required: Any = Column(Float, nullable=False)
    water_saved: Any = Column(Float, nullable=False)
    created_at: Any = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="irrigation_records")


# ── EXTENDED ML & IOT MODELS ──────────────────────────────────────────

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id: Any = Column(Integer, primary_key=True, index=True)
    device_id: Any = Column(String, default="ESP32_FIELD_01", index=True)
    timestamp: Any = Column(DateTime, server_default=func.now(), index=True)
    soil_moisture: Any = Column(Float, nullable=False)
    temperature: Any = Column(Float, nullable=False)
    humidity: Any = Column(Float, nullable=False)
    rainfall: Any = Column(Float, default=0.0)
    wind_speed: Any = Column(Float, default=0.0)
    soil_type: Any = Column(String, default="loam")
    crop_type: Any = Column(String, default="Samba Rice")
    hydrogel_present: Any = Column(Integer, default=1)  # 1 = True, 0 = False
    hydrogel_dosage: Any = Column(Float, default=50.0)  # g/m²
    pump_status: Any = Column(String, default="OFF")
    created_at: Any = Column(DateTime, server_default=func.now())


class IrrigationEvent(Base):
    __tablename__ = "irrigation_events"
    id: Any = Column(Integer, primary_key=True, index=True)
    user_id: Any = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp: Any = Column(DateTime, server_default=func.now(), index=True)
    decision_mode: Any = Column(String, nullable=False)  # 'rule_based' or 'ml_predictive'
    trigger_reason: Any = Column(String, nullable=False)
    water_amount_litres: Any = Column(Float, nullable=False)
    duration_minutes: Any = Column(Float, nullable=False)
    status: Any = Column(String, default="completed")  # 'completed', 'simulated', 'aborted'
    pump_id: Any = Column(String, default="PUMP_MAIN")
    created_at: Any = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="irrigation_events")


class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    id: Any = Column(Integer, primary_key=True, index=True)
    timestamp: Any = Column(DateTime, server_default=func.now(), index=True)
    model_name: Any = Column(String, nullable=False)
    model_version: Any = Column(String, default="v1.0")
    current_moisture: Any = Column(Float, nullable=False)
    predicted_1h: Any = Column(Float, nullable=False)
    predicted_3h: Any = Column(Float, nullable=False)
    predicted_6h: Any = Column(Float, nullable=False)
    target_moisture: Any = Column(Float, default=65.0)
    irrigation_required: Any = Column(Integer, default=0)  # 1 = True, 0 = False
    water_required_litres: Any = Column(Float, default=0.0)
    confidence_score: Any = Column(Float, nullable=True)
    decision_mode: Any = Column(String, default="ml_predictive")
    created_at: Any = Column(DateTime, server_default=func.now())

    feedback = relationship("PredictionFeedback", back_populates="prediction")


class MLModelVersion(Base):
    __tablename__ = "ml_model_versions"
    id: Any = Column(Integer, primary_key=True, index=True)
    model_name: Any = Column(String, nullable=False)
    version_tag: Any = Column(String, unique=True, nullable=False)
    algorithm: Any = Column(String, nullable=False)
    target_variable: Any = Column(String, nullable=False)
    mae: Any = Column(Float, nullable=True)
    rmse: Any = Column(Float, nullable=True)
    r2_score: Any = Column(Float, nullable=True)
    accuracy: Any = Column(Float, nullable=True)
    f1_score: Any = Column(Float, nullable=True)
    hyperparameters: Any = Column(String, nullable=True)
    is_active: Any = Column(Integer, default=1)  # 1 = True, 0 = False
    trained_at: Any = Column(DateTime, server_default=func.now())


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"
    id: Any = Column(Integer, primary_key=True, index=True)
    timestamp: Any = Column(DateTime, server_default=func.now(), index=True)
    sensor_id: Any = Column(String, default="ESP32_FIELD_01")
    anomaly_type: Any = Column(String, nullable=False)  # 'impossible_value', 'sudden_spike', 'sensor_freeze', 'pump_no_response'
    severity: Any = Column(String, default="WARNING")  # 'INFO', 'WARNING', 'CRITICAL'
    value_recorded: Any = Column(Float, nullable=True)
    threshold_expected: Any = Column(String, nullable=True)
    description: Any = Column(String, nullable=False)
    resolved: Any = Column(Integer, default=0)  # 1 = True, 0 = False
    created_at: Any = Column(DateTime, server_default=func.now())


class PredictionFeedback(Base):
    __tablename__ = "prediction_feedback"
    id: Any = Column(Integer, primary_key=True, index=True)
    prediction_id: Any = Column(Integer, ForeignKey("ml_predictions.id"), nullable=True)
    horizon_hours: Any = Column(Integer, default=1)  # 1, 3, or 6
    predicted_moisture: Any = Column(Float, nullable=False)
    actual_moisture: Any = Column(Float, nullable=False)
    absolute_error: Any = Column(Float, nullable=False)
    relative_error_pct: Any = Column(Float, nullable=False)
    created_at: Any = Column(DateTime, server_default=func.now())

    prediction = relationship("MLPrediction", back_populates="feedback")


class UserPlant(Base):
    __tablename__ = "user_plants"
    id: Any = Column(Integer, primary_key=True, index=True)
    user_id: Any = Column(Integer, ForeignKey("users.id"), nullable=True)
    name: Any = Column(String, nullable=False)
    plant_type: Any = Column(String, nullable=False)
    variety: Any = Column(String, nullable=True)
    container_size_litres: Any = Column(Float, default=15.0)
    planting_date: Any = Column(String, nullable=True)
    growth_stage: Any = Column(String, default="Vegetative")
    hydrogel_dosage_grams: Any = Column(Float, default=25.0)
    health_status: Any = Column(String, default="Healthy")
    notes: Any = Column(String, nullable=True)
    created_at: Any = Column(DateTime, server_default=func.now())

    observations = relationship("PlantObservation", back_populates="plant", cascade="all, delete-orphan")


class PlantObservation(Base):
    __tablename__ = "plant_observations"
    id: Any = Column(Integer, primary_key=True, index=True)
    plant_id: Any = Column(Integer, ForeignKey("user_plants.id"), nullable=False)
    observation_type: Any = Column(String, default="General")
    notes: Any = Column(String, nullable=False)
    severity: Any = Column(String, default="Normal")
    created_at: Any = Column(DateTime, server_default=func.now())

    plant = relationship("UserPlant", back_populates="observations")
