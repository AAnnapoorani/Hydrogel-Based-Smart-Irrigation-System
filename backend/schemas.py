# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Soil ──
class SoilInput(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    organic_carbon: float
    soil_texture: Optional[str] = "loam"

class SoilAnalysisResult(BaseModel):
    fertility_score: float
    classification: str
    nutrient_scores: dict
    recommended_crops: List[dict]
    recommendations: List[str]

class SoilRecord(BaseModel):
    id: int
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    organic_carbon: float
    fertility_score: float
    classification: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True) 


# ── Irrigation ──
class IrrigationInput(BaseModel):
    sm_current: float
    sm_optimal: float
    alpha: float = 0.85
    field_area: float = 500

class IrrigationResult(BaseModel):
    smd: float
    irrigation_required: float
    total_water_litres: float
    water_saved: float
    efficiency_rating: str

class ScheduleRequest(BaseModel):
    irrigation_required: float
    field_area: float
    hours_from_now: int = 12

class IrrigationRecord(BaseModel):
    id: int
    sm_current: float
    sm_optimal: float
    smd: float
    irrigation_required: float
    water_saved: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Sensors ──
class SensorReadingCreate(BaseModel):
    device_id: Optional[str] = "ESP32_FIELD_01"
    soil_moisture: float
    temperature: float
    humidity: float
    rainfall: Optional[float] = 0.0
    wind_speed: Optional[float] = 0.0
    soil_type: Optional[str] = "loam"
    crop_type: Optional[str] = "Samba Rice"
    hydrogel_present: Optional[int] = 1
    hydrogel_dosage: Optional[float] = 50.0
    pump_status: Optional[str] = "OFF"

class SensorReadingOut(BaseModel):
    id: int
    device_id: str
    timestamp: datetime
    soil_moisture: float
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    soil_type: str
    crop_type: str
    hydrogel_present: int
    hydrogel_dosage: float
    pump_status: str
    created_at: datetime
    is_online: Optional[bool] = False
    seconds_ago: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class NodeStatusOut(BaseModel):
    device_id: str = "ESP32_FIELD_01"
    is_online: bool = False
    status: str = "OFFLINE"
    status_label: str = "ESP32 Offline (Disconnected)"
    last_seen: Optional[datetime] = None
    seconds_since_last_reading: Optional[float] = None
    heartbeat_timeout_seconds: int = 60
    packets_received_session: int = 0
    signal_strength: str = "DISCONNECTED"
    rssi_dbm: Optional[int] = None
    battery_level_pct: Optional[float] = None
    pump_status: str = "OFF"
    soil_moisture: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    message: str = "ESP32 Node is Disconnected. No active telemetry stream detected."

class HeartbeatInput(BaseModel):
    device_id: Optional[str] = "ESP32_FIELD_01"
    firmware_version: Optional[str] = "v2.0"
    rssi_dbm: Optional[int] = -65
    battery_level_pct: Optional[float] = 95.0



# ── ML Forecasting & Inference ──
class MoisturePredictionInput(BaseModel):
    current_moisture: float
    temperature: float
    humidity: float
    rainfall: Optional[float] = 0.0
    wind_speed: Optional[float] = 10.0
    soil_type: Optional[str] = "loam"
    crop_type: Optional[str] = "Samba Rice"
    hydrogel_present: Optional[int] = 1
    hours_since_irrigation: Optional[float] = 12.0
    target_moisture: Optional[float] = 65.0

class MoisturePredictionOutput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    current_moisture: float
    predicted_1h: float
    predicted_3h: float
    predicted_6h: float
    target_moisture: float
    model_name: str
    model_version: str
    confidence_score: Optional[float] = None
    feature_importance: Optional[dict] = None

class CropPredictionInput(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    organic_carbon: float
    temperature: Optional[float] = 30.0
    humidity: Optional[float] = 70.0
    rainfall: Optional[float] = 100.0
    soil_type: Optional[str] = "loam"

class CropProbability(BaseModel):
    crop: str
    probability: float

class CropPredictionOutput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    recommended_crop: str
    confidence: float
    top_candidates: List[CropProbability]
    model_name: str

class AnomalyCheckInput(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float
    pump_status: Optional[str] = "OFF"
    previous_moisture: Optional[float] = None

class AnomalyCheckOutput(BaseModel):
    is_anomaly: bool
    status: str  # 'NORMAL' or 'ANOMALY'
    anomaly_type: Optional[str] = None
    severity: Optional[str] = None
    description: str


# ── Predictive Decision Engine ──
class PredictiveDecisionInput(BaseModel):
    current_moisture: float
    target_moisture: Optional[float] = 60.0
    temperature: float
    humidity: float
    rainfall_forecast_6h: Optional[float] = None
    wind_speed: Optional[float] = 12.0
    soil_texture: Optional[str] = "cocopeat_mix"
    crop_type: Optional[str] = "Potted Tomato"
    hydrogel_present: Optional[int] = 1
    field_area: Optional[float] = 10.0
    pot_count: Optional[int] = 10
    container_volume_litres: Optional[float] = 15.0
    hours_since_irrigation: Optional[float] = 18.0

class DecisionComparison(BaseModel):
    rule_based_decision: bool
    rule_based_water_litres: float
    rule_based_water_ml: Optional[float] = None
    rule_based_smd: float
    ml_predictive_decision: bool
    ml_predictive_water_litres: float
    ml_predictive_water_ml: Optional[float] = None
    predicted_moisture_3h: float
    predicted_moisture_6h: float
    water_difference_litres: float
    water_difference_ml: Optional[float] = None
    water_saving_advantage_pct: float
    water_per_pot_ml: Optional[float] = None

class PredictiveDecisionOutput(BaseModel):
    current_moisture: float
    predicted_moisture_1h: float
    predicted_moisture_3h: float
    predicted_moisture_6h: float
    target_moisture: float
    irrigation_required: bool
    water_required_litres: float
    water_required_ml: Optional[float] = None
    water_per_pot_ml: Optional[float] = None
    pot_count: Optional[int] = 10
    irrigation_unit: str = "mL"
    estimated_pump_duration_minutes: float
    decision_mode: str
    confidence: Optional[float] = None
    reason: str
    hydrogel_buffering_active: bool
    comparison: DecisionComparison

class PumpExecutionInput(BaseModel):
    duration_minutes: float
    water_amount_litres: float
    water_amount_ml: Optional[float] = None
    decision_mode: str = "ml_predictive"
    trigger_reason: str = "Automated predictive deficit"
    simulation_mode: bool = True

class PumpExecutionOutput(BaseModel):
    status: str
    pump_state: str
    mode: str
    duration_minutes: float
    water_amount_litres: float
    water_amount_ml: Optional[float] = None
    timestamp: datetime
    message: str


# ── Feedback Loop ──
class FeedbackCreate(BaseModel):
    prediction_id: Optional[int] = None
    horizon_hours: int = 1
    predicted_moisture: float
    actual_moisture: float

class FeedbackOut(BaseModel):
    id: int
    horizon_hours: int
    predicted_moisture: float
    actual_moisture: float
    absolute_error: float
    relative_error_pct: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ModelComparisonOut(BaseModel):
    models: List[dict]
    best_model: str
    evaluation_date: str


# ── TERRACE GARDEN PLANT RECOMMENDER SCHEMAS ──
class TerraceRecommenderInput(BaseModel):
    terrace_area_sqm: Optional[float] = 20.0
    pot_count: Optional[int] = 10
    sunlight_hours: str = "4-6h"  # "<3h", "3-5h", "6+h"
    container_size_litres: Optional[float] = 15.0  # 5, 10, 15, 20, 25+
    soil_type: str = "cocopeat_mix"  # "cocopeat_mix", "red_soil_compost", "garden_soil", "potting_mix"
    season: str = "post_monsoon"  # "summer", "sw_monsoon", "ne_monsoon", "winter", "post_monsoon"
    water_availability: str = "moderate"  # "limited", "moderate", "abundant"
    experience_level: str = "beginner"  # "beginner", "intermediate", "advanced"
    preferred_categories: List[str] = ["vegetables", "herbs"]
    maintenance_level: str = "moderate"  # "low", "moderate", "high"
    gardening_purposes: List[str] = ["household_consumption", "cooking_herbs"]
    hydrogel_present: Optional[bool] = True

class RecommendedPlant(BaseModel):
    id: str
    name: str
    scientific_name: str
    tamil_name: Optional[str] = None
    category: str
    suitability_score: float
    suitability_rating: str
    why_suitable: str
    sunlight_requirement: str
    min_container_litres: float
    recommended_pot_depth_inches: float
    watering_needs: str
    hydrogel_synergy: str
    soil_medium_preference: str
    growth_timeline_days: str
    difficulty_level: str
    seasonal_notes: str
    care_instructions: List[str]
    companion_plants: List[str]
    potential_challenges: str

class UnsuitablePlantWarning(BaseModel):
    plant_name: str
    limiting_factor: str
    explanation: str
    recommended_alternative: str

class TerraceRecommenderOutput(BaseModel):
    total_evaluated: int
    recommended_plants: List[RecommendedPlant]
    unsuitable_warnings: List[UnsuitablePlantWarning]
    terrace_context_summary: str
    hydrogel_recommendation: str


# ── PLANT HEALTH & PEST DIAGNOSIS SCHEMAS ──
class DiseaseCandidate(BaseModel):
    condition: str
    scientific_name: Optional[str] = None
    confidence_score: float
    category: str  # "Fungal", "Bacterial", "Viral", "Physiological", "Healthy"

class VerificationStep(BaseModel):
    step_number: int
    action: str
    visual_clue: str

class PlantDiagnosisOutput(BaseModel):
    status: str  # "conclusive", "inconclusive", "healthy", "error"
    plant_species_identified: Optional[str] = None
    primary_condition: str
    confidence: float
    alternative_predictions: List[DiseaseCandidate]
    is_conclusive: bool
    visible_symptoms: List[str]
    possible_causes: List[str]
    verification_steps: List[VerificationStep]
    organic_remediation: List[str]
    chemical_alternative: Optional[str] = None
    hydrogel_irrigation_advisory: str
    scientific_disclaimer: str
    image_metadata: Optional[dict] = None

class PestCandidate(BaseModel):
    pest_name: str
    scientific_name: Optional[str] = None
    confidence_score: float
    detection_type: str  # "Direct Insect Detection" or "Secondary Leaf Damage Inference"
    severity_level: str  # "Low", "Moderate", "Critical"

class PestDiagnosisOutput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    status: str  # "pest_detected", "ambiguous_damage", "no_pest_found", "inconclusive"
    primary_pest: str
    confidence: float
    detection_type: str
    alternative_pests: List[PestCandidate]
    is_conclusive: bool
    visible_evidence: List[str]
    typical_damage_symptoms: List[str]
    affected_plant_parts: List[str]
    inspection_steps: List[str]
    organic_management: List[str]
    preventive_measures: List[str]
    follow_up_monitoring: str
    scientific_disclaimer: str
    pest_count: Optional[int] = None
    bounding_boxes: Optional[List[Dict[str, Any]]] = None
    annotated_image_base64: Optional[str] = None
    model_architecture: Optional[str] = "YOLOv8-Nano (yolov8n - 3.2M parameters)"


# ── SOIL HEALTH MONITORING SCHEMAS ──
class NutrientReadingDetail(BaseModel):
    parameter: str
    reading_value: float
    unit: str
    status: str  # "Deficient", "Optimal", "Excessive"
    calibrated_range: str
    sensor_tolerance: str
    interpretation: str
    organic_remediation: Optional[str] = None

class SoilHealthMonitoringOutput(BaseModel):
    container_potting_mix: str
    overall_fertility_index: float
    fertility_grade: str
    readings: List[NutrientReadingDetail]
    hydrogel_retention_effect: str
    plant_specific_advisories: List[dict]
    sensor_accuracy_notice: str


# ── PERSONALIZED PLANT CARE ASSISTANT SCHEMAS ──
class PlantCareAdvisoryOutput(BaseModel):
    plant_name: str
    growth_stage: str
    watering_urgency: str  # "Not Needed", "Moderate Need", "Immediate Replenishment"
    watering_volume_ml: float
    hydrogel_status: str
    yellowing_diagnostic_tree: List[str]
    temperature_humidity_stress_alert: Optional[str] = None
    nutrient_adjustment: Optional[str] = None
    immediate_actions: List[str]
    upcoming_3_day_watch: List[str]


# ── UNIFIED PLANT DASHBOARD SCHEMAS ──
class UserPlantCreate(BaseModel):
    name: str
    plant_type: str
    variety: Optional[str] = None
    container_size_litres: float = 15.0
    planting_date: Optional[str] = None
    growth_stage: str = "Vegetative"  # "Seedling", "Vegetative", "Flowering", "Fruiting", "Mature"
    hydrogel_dosage_grams: float = 25.0
    notes: Optional[str] = None

class UserPlantOut(BaseModel):
    id: int
    name: str
    plant_type: str
    variety: Optional[str] = None
    container_size_litres: float
    planting_date: Optional[str] = None
    growth_stage: str
    hydrogel_dosage_grams: float
    health_status: str
    notes: Optional[str] = None
    created_at: datetime
    latest_moisture: Optional[float] = None
    latest_diagnosis: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class PlantObservationCreate(BaseModel):
    plant_id: int
    observation_type: str  # "Leaf Color", "Wilting", "New Growth", "Pest Sighting", "Flowering", "General"
    notes: str
    severity: Optional[str] = "Normal"  # "Normal", "Mild", "Severe"

class PlantObservationOut(BaseModel):
    id: int
    plant_id: int
    observation_type: str
    notes: str
    severity: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

