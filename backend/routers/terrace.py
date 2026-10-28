"""Terrace Gardening Router for IRRIGATEWISE.

Endpoints for:
- Terrace garden plant recommendation with multi-criteria constraint satisfaction
- Botanical container catalog lookup
- Plant health disease diagnosis (Module 1)
- Pest identification & management (Module 2)
- Container soil nutrient interpretation (Module 3)
- Personalized plant care assistant (Module 5)
- Registered terrace plants and observations (Module 7)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, List
from sqlalchemy.orm import Session

from database import get_db
import schemas
from services.terrace_recommender import TerraceRecommenderService, TERRACE_PLANTS_CATALOG

router = APIRouter(prefix="/terrace", tags=["Terrace Gardening Intelligence"])

@router.post("/recommend", response_model=schemas.TerraceRecommenderOutput)
def recommend_terrace_plants(payload: schemas.TerraceRecommenderInput):
    """Recommends suitable potted container plants for terrace gardens based on

    sunlight, pot sizes, growing medium, season, experience, and hydrogel status.
    """
    return TerraceRecommenderService.recommend(payload)

@router.get("/catalog")
def get_terrace_catalog(category: Optional[str] = None):
    """Returns curated botanical details for all 24 supported terrace container species."""
    if category:
        filtered = [
            p for p in TERRACE_PLANTS_CATALOG 
            if p["category"].lower() == category.lower()
        ]
        return {"total": len(filtered), "plants": filtered}
    return {"total": len(TERRACE_PLANTS_CATALOG), "plants": TERRACE_PLANTS_CATALOG}


# ── MODULE 1: PLANT HEALTH DISEASE DIAGNOSIS ──
@router.post("/diagnosis/disease", response_model=schemas.PlantDiagnosisOutput)
async def diagnose_plant_disease(
    file: UploadFile = File(...),
    plant_hint: Optional[str] = Form(None),
    symptom_hint: Optional[str] = Form(None),
    duration_days: Optional[int] = Form(None)
):
    """Analyzes an uploaded leaf photograph for common terrace plant diseases."""
    from services.plant_health_service import PlantHealthService

    content = await file.read()
    valid, msg, img = PlantHealthService.validate_image_file(file.filename or "upload.jpg", content)
    if not valid or img is None:
        raise HTTPException(status_code=400, detail=msg)
    
    return PlantHealthService.analyze_plant_disease(
        image=img,
        plant_hint=plant_hint,
        symptom_hint=symptom_hint,
        duration_days=duration_days
    )


# ── MODULE 2: PEST IDENTIFICATION & MANAGEMENT ──
@router.post("/diagnosis/pest", response_model=schemas.PestDiagnosisOutput)
async def diagnose_plant_pests(
    file: UploadFile = File(...),
    plant_hint: Optional[str] = Form(None),
    symptom_hint: Optional[str] = Form(None)
):
    """Analyzes an uploaded photograph for garden insect pests and feeding damage."""
    from services.plant_health_service import PlantHealthService

    content = await file.read()
    valid, msg, img = PlantHealthService.validate_image_file(file.filename or "upload.jpg", content)
    if not valid or img is None:
        raise HTTPException(status_code=400, detail=msg)
    
    return PlantHealthService.analyze_pests(
        image=img,
        plant_hint=plant_hint,
        symptom_hint=symptom_hint,
        filename=file.filename
    )


# ── MODULE 3: CONTAINER SOIL HEALTH & NUTRIENT INTERPRETATION ──
@router.get("/soil/interpretation", response_model=schemas.SoilHealthMonitoringOutput)
def interpret_soil_get(
    nitrogen: float = 95.0,
    phosphorus: float = 45.0,
    potassium: float = 210.0,
    ph: float = 6.4,
    organic_carbon: Optional[float] = 0.85,
    moisture: Optional[float] = 58.0,
    plant_type: Optional[str] = "Tomato",
    growth_stage: Optional[str] = "Vegetative",
    hydrogel_present: bool = True
):
    """Evaluates NPK and pH readings against 15L container potting mix benchmarks."""
    from services.soil_health_service import SoilHealthService
    return SoilHealthService.evaluate_potting_mix(
        nitrogen=nitrogen,
        phosphorus=phosphorus,
        potassium=potassium,
        ph=ph,
        organic_carbon=organic_carbon,
        moisture=moisture,
        plant_type=plant_type,
        growth_stage=growth_stage,
        hydrogel_present=hydrogel_present
    )

@router.post("/soil/evaluate", response_model=schemas.SoilHealthMonitoringOutput)
def interpret_soil_post(
    payload: schemas.SoilInput,
    plant_type: Optional[str] = "Tomato",
    growth_stage: Optional[str] = "Vegetative",
    moisture: Optional[float] = 58.0,
    hydrogel_present: bool = True
):
    """POST payload evaluator for container potting mix testing."""
    from services.soil_health_service import SoilHealthService
    return SoilHealthService.evaluate_potting_mix(
        nitrogen=payload.nitrogen,
        phosphorus=payload.phosphorus,
        potassium=payload.potassium,
        ph=payload.ph,
        organic_carbon=payload.organic_carbon,
        moisture=moisture,
        plant_type=plant_type,
        growth_stage=growth_stage,
        hydrogel_present=hydrogel_present
    )


# ── MODULE 5: PERSONALIZED PLANT CARE ASSISTANT ──
class CareAdvisoryRequest(schemas.BaseModel):
    plant_name: str = "Tomato"
    growth_stage: str = "Vegetative"
    current_moisture: float = 52.0
    temperature: float = 31.0
    humidity: float = 65.0
    forecast_rain_mm: float = 0.0
    hydrogel_present: bool = True
    yellowing_observed: bool = False

@router.post("/care/advisory", response_model=schemas.PlantCareAdvisoryOutput)
def get_care_advisory(req: CareAdvisoryRequest):
    """Synthesizes container plant biology, telemetry, and growth stage into daily care advice."""
    from services.plant_care_assistant import PlantCareAssistant
    return PlantCareAssistant.generate_advisory(
        plant_name=req.plant_name,
        growth_stage=req.growth_stage,
        current_moisture=req.current_moisture,
        temperature=req.temperature,
        humidity=req.humidity,
        forecast_rain_mm=req.forecast_rain_mm,
        hydrogel_present=req.hydrogel_present,
        yellowing_observed=req.yellowing_observed
    )


# ── MODULE 7: UNIFIED PLANT PROFILE REGISTRY & OBSERVATION LOGS ──
@router.get("/plants", response_model=List[schemas.UserPlantOut])
def list_user_plants(db: Session = Depends(get_db)):
    """Retrieves all registered terrace garden container plants."""
    import models
    plants = db.query(models.UserPlant).order_by(models.UserPlant.id.asc()).all()
    # Enrich with latest live sensor moisture if available
    latest_sensor = db.query(models.SensorReading).order_by(models.SensorReading.timestamp.desc()).first()
    latest_sm = latest_sensor.soil_moisture if latest_sensor else 58.0

    res = []
    for p in plants:
        p_dict = {
            "id": p.id,
            "name": p.name,
            "plant_type": p.plant_type,
            "variety": p.variety,
            "container_size_litres": p.container_size_litres,
            "planting_date": p.planting_date,
            "growth_stage": p.growth_stage,
            "hydrogel_dosage_grams": p.hydrogel_dosage_grams,
            "health_status": p.health_status,
            "notes": p.notes,
            "created_at": p.created_at,
            "latest_moisture": latest_sm,
            "latest_diagnosis": "No active foliar disease detected"
        }
        res.append(schemas.UserPlantOut(**p_dict))
    return res

@router.post("/plants", response_model=schemas.UserPlantOut)
def create_user_plant(payload: schemas.UserPlantCreate, db: Session = Depends(get_db)):
    """Registers a new container plant or grow bag in the terrace garden."""
    import models
    new_plant = models.UserPlant(
        name=payload.name,
        plant_type=payload.plant_type,
        variety=payload.variety,
        container_size_litres=payload.container_size_litres,
        planting_date=payload.planting_date,
        growth_stage=payload.growth_stage,
        hydrogel_dosage_grams=payload.hydrogel_dosage_grams,
        notes=payload.notes
    )
    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)
    return schemas.UserPlantOut(
        id=new_plant.id,
        name=new_plant.name,
        plant_type=new_plant.plant_type,
        variety=new_plant.variety,
        container_size_litres=new_plant.container_size_litres,
        planting_date=new_plant.planting_date,
        growth_stage=new_plant.growth_stage,
        hydrogel_dosage_grams=new_plant.hydrogel_dosage_grams,
        health_status=new_plant.health_status,
        notes=new_plant.notes,
        created_at=new_plant.created_at,
        latest_moisture=58.0,
        latest_diagnosis="Healthy"
    )

@router.delete("/plants/{plant_id}")
def delete_user_plant(plant_id: int, db: Session = Depends(get_db)):
    """Removes a container plant from the registry."""
    import models
    plant = db.query(models.UserPlant).filter(models.UserPlant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    db.delete(plant)
    db.commit()
    return {"message": f"Plant {plant_id} deleted successfully"}

@router.get("/plants/{plant_id}/observations", response_model=List[schemas.PlantObservationOut])
def get_plant_observations(plant_id: int, db: Session = Depends(get_db)):
    """Returns historical visual observations and growth records for a specific pot."""
    import models
    return db.query(models.PlantObservation).filter(models.PlantObservation.plant_id == plant_id).order_by(models.PlantObservation.created_at.desc()).all()

@router.post("/plants/{plant_id}/observations", response_model=schemas.PlantObservationOut)
def add_plant_observation(plant_id: int, payload: schemas.PlantObservationCreate, db: Session = Depends(get_db)):
    """Logs a physical observation (e.g. leaf yellowing, flowering, pest sighting) for a pot."""
    import models
    plant = db.query(models.UserPlant).filter(models.UserPlant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    
    obs = models.PlantObservation(
        plant_id=plant_id,
        observation_type=payload.observation_type,
        notes=payload.notes,
        severity=payload.severity or "Normal"
    )
    db.add(obs)
    # If severe pest or disease noted, update plant health_status
    if payload.severity == "Severe":
        plant.health_status = f"Attention: {payload.observation_type}"
    db.commit()
    db.refresh(obs)
    return obs
