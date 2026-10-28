# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware  
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from database import get_db, engine
import models, schemas
from logic import SoilAnalyzer, IrrigationCalculator
from routers import sensors, ml, irrigation, reports, weather, terrace
from services.websocket_manager import ws_manager

models.Base.metadata.create_all(bind=engine)

app = FastAPI( title="IrrigateWise API", version="2.0.0", description="ML-Driven Predictive Irrigation & Agricultural Intelligence System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend.vercel.app", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount v1 API routers
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(ml.router, prefix="/api/v1")
app.include_router(irrigation.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(weather.router, prefix="/api/v1")
app.include_router(terrace.router, prefix="/api/v1")

# WebSocket Real-Time Telemetry Stream
@app.websocket("/api/v1/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event":"PONG"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# ── SOIL ──────────────────────────────────────────────────────────
@app.post("/soil/analyze", response_model=schemas.SoilAnalysisResult)
def analyze_soil(
    payload: schemas.SoilInput,
    db: Session = Depends(get_db),
):
    result = SoilAnalyzer.analyze(payload)
    # Persist analysis to database for default record (id=1)
    try:
        user = db.query(models.User).filter(models.User.id == 1).first()
        if user:
            rec = models.SoilData(
                user_id=user.id,
                nitrogen=payload.nitrogen,
                phosphorus=payload.phosphorus,
                potassium=payload.potassium,
                ph=payload.ph,
                organic_carbon=payload.organic_carbon,
                fertility_score=result.fertility_score,
                classification=result.classification,
                created_at=datetime.now(timezone.utc)
            )
            db.add(rec)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Failed to persist soil record: {e}")
    return result


@app.get("/soil/history", response_model=List[schemas.SoilRecord])
def soil_history(
    db: Session = Depends(get_db),
):
    return db.query(models.SoilData).order_by(models.SoilData.created_at.desc()).limit(50).all()


# ── IRRIGATION ────────────────────────────────────────────────────
@app.post("/irrigation/calculate", response_model=schemas.IrrigationResult)
def calculate_irrigation(
    payload: schemas.IrrigationInput,
    db: Session = Depends(get_db),
):
    result = IrrigationCalculator.calculate(payload)
    try:
        user = db.query(models.User).filter(models.User.id == 1).first()
        if user:
            rec = models.IrrigationData(
                user_id=user.id,
                sm_current=payload.sm_current,
                sm_optimal=payload.sm_optimal,
                smd=result.smd,
                irrigation_required=result.irrigation_required,
                water_saved=result.water_saved,
                created_at=datetime.now(timezone.utc)
            )
            db.add(rec)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Failed to persist irrigation record: {e}")
    return result


@app.post("/irrigation/schedule")
def schedule_irrigation(
    payload: schemas.ScheduleRequest,
    db: Session = Depends(get_db),
):
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=payload.hours_from_now)
    return {
        "message": "Irrigation scheduled successfully",
        "scheduled_at": scheduled_at.isoformat(),
        "field_area": payload.field_area,
        "irrigation_required": payload.irrigation_required,
    }


@app.get("/irrigation/history", response_model=List[schemas.IrrigationRecord])
def irrigation_history(
    db: Session = Depends(get_db),
):
    return db.query(models.IrrigationData).order_by(models.IrrigationData.created_at.desc()).limit(50).all()


# ── REPORTS ───────────────────────────────────────────────────────
@app.get("/reports")
def get_reports(
    db: Session = Depends(get_db),
):
    soil = db.query(models.SoilData).order_by(models.SoilData.created_at.desc()).limit(20).all()
    irr = db.query(models.IrrigationData).order_by(models.IrrigationData.created_at.desc()).limit(20).all()
    return {
        "soil_records": [
            {
                "id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "nitrogen": s.nitrogen,
                "phosphorus": s.phosphorus,
                "potassium": s.potassium,
                "ph": s.ph,
                "organic_carbon": s.organic_carbon,
                "fertility_score": s.fertility_score,
                "classification": s.classification
            }
            for s in soil
        ],
        "irrigation_records": [
            {
                "id": i.id,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "sm_current": i.sm_current,
                "sm_optimal": i.sm_optimal,
                "smd": i.smd,
                "irrigation_required": i.irrigation_required,
                "water_saved": i.water_saved
            }
            for i in irr
        ]
    }

@app.get("/reports/export")
def export_reports(
    db: Session = Depends(get_db),
):
    return {
        "message": "CSV reports ready for download",
        "download_url": "/api/v1/reports/export/soil-csv",
        "irrigation_download_url": "/api/v1/reports/export/irrigation-csv",
        "expires_in": 3600,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "IrrigateWise ML & IoT Agricultural Engine",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
