from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Auth ──
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    token: str
    user: UserOut


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
    class Config:
        from_attributes = True 


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
    class Config:
        from_attributes = True
