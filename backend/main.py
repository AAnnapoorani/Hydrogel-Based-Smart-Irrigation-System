from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
import bcrypt

from database import get_db, engine
import models, schemas
from logic import SoilAnalyzer, IrrigationCalculator

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IrrigateWise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
SECRET_KEY = "irrigatewise-secret-key-change-in-prod"
ALGORITHM = "HS256"


def create_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(days=30)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── AUTH ──────────────────────────────────────────────────────────
@app.post("/register", response_model=schemas.TokenResponse)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    user = models.User(name=payload.name, email=payload.email, password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id), "user": user}


@app.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not bcrypt.checkpw(payload.password.encode(), user.password.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_token(user.id), "user": user}


# ── SOIL ──────────────────────────────────────────────────────────
@app.post("/soil/analyze", response_model=schemas.SoilAnalysisResult)
def analyze_soil(
    payload: schemas.SoilInput,
    db: Session = Depends(get_db),
):
    result = SoilAnalyzer.analyze(payload)
    # Only save to DB if a valid user is logged in
    # Skipping DB save for now (no auth required in demo mode)
    return result


@app.get("/soil/history", response_model=List[schemas.SoilRecord])
def soil_history(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return db.query(models.SoilData).filter(models.SoilData.user_id == user.id).order_by(models.SoilData.created_at.desc()).limit(50).all()


# ── IRRIGATION ────────────────────────────────────────────────────
@app.post("/irrigation/calculate", response_model=schemas.IrrigationResult)
def calculate_irrigation(
    payload: schemas.IrrigationInput,
    db: Session = Depends(get_db),
):
    result = IrrigationCalculator.calculate(payload)
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
    user: models.User = Depends(get_current_user),
):
    return db.query(models.IrrigationData).filter(models.IrrigationData.user_id == user.id).order_by(models.IrrigationData.created_at.desc()).limit(50).all()


# ── REPORTS ───────────────────────────────────────────────────────
@app.get("/reports")
def get_reports(
    db: Session = Depends(get_db),
):
    return {"soil_records": [], "irrigation_records": []}

@app.get("/reports/export")
def export_reports(
    db: Session = Depends(get_db),
):
    filename = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return {
        "message": "Export initiated",
        "download_url": f"/exports/{filename}",
        "expires_in": 3600,
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
