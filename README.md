# IrrigateWise – Smart Irrigation Platform

📍 Built for Erumaiyur Village, Tambaram, Tamil Nadu  
🌾 Soil Analysis · Crop Recommendation · Water Optimization

## Overview

**IrrigateWise** is a smart irrigation platform designed to support data-driven agricultural decisions through soil analysis, crop recommendations, and optimized irrigation planning.

The platform combines a **Next.js frontend**, **FastAPI backend**, and **PostgreSQL database**, with intelligent logic for soil fertility scoring and irrigation requirement estimation.

---

## Folder Structure

```text
irrigatewise/
├── docker-compose.yml
├── seed.sql
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── logic.py
│   └── database.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.js
    ├── next.config.js
    ├── .env.example
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx
        │   ├── dashboard/
        │   │   └── page.tsx
        │   ├── soil/
        │   │   └── page.tsx
        │   ├── irrigation/
        │   │   └── page.tsx
        │   └── reports/
        │       └── page.tsx
        ├── components/
        │   ├── Navbar.tsx
        │   ├── StatCard.tsx
        │   └── WeatherWidget.tsx
        └── lib/
            └── api.ts
```

---

## Environment Variables

### Backend

Create `backend/.env` locally using the following template:

```env
DATABASE_URL=<your-postgresql-connection-string>
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30
```

### Frontend

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Security:** Never commit `.env` or `.env.local` files containing real credentials, passwords, API keys, tokens, or secret keys. Use `.env.example` files for documentation.

---

## Local Development

### Prerequisites

- Docker + Docker Compose
- Node.js 20+
- Python 3.12+
- PostgreSQL 16+ (if running without Docker)

### Option 1: Docker

```bash
git clone <your-repository-url>
cd irrigatewise

docker-compose up --build
```

After the containers are running, seed the database with the provided sample data:

```bash
docker exec -it <database-container-name> \
psql -U <database-user> -d <database-name> -f /seed.sql
```

Open the application:

```text
http://localhost:3000
```

Backend API documentation:

```text
http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend

python -m venv venv
```

Activate the virtual environment.

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables and start the backend:

```bash
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

npm install
npm install leaflet react-leaflet

npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/register` | No | Register a new user |
| POST | `/login` | No | Authenticate user and return JWT |
| POST | `/soil/analyze` | Yes | Analyze soil parameters |
| GET | `/soil/history` | Yes | Retrieve soil analysis history |
| POST | `/irrigation/calculate` | Yes | Calculate irrigation requirement |
| POST | `/irrigation/schedule` | Yes | Schedule irrigation |
| GET | `/irrigation/history` | Yes | Retrieve irrigation history |
| GET | `/reports` | Yes | Retrieve combined report data |
| GET | `/reports/export` | Yes | Generate/export report |
| GET | `/health` | No | Check API health |

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## Core Logic

### Soil Fertility Score

The soil fertility score combines normalized nutrient and soil-property scores:

```text
Score =
    N_score  × 0.30
  + P_score  × 0.20
  + K_score  × 0.20
  + pH_score × 0.15
  + OC_score × 0.15
```

Classification:

```text
Score ≥ 70        → High
45 ≤ Score < 70  → Medium
Score < 45       → Low
```

### Irrigation Requirement

Soil moisture deficit:

```text
SMD = SM_optimal − SM_current
```

Irrigation requirement:

```text
IR = α × SMD
```

where `α` represents the soil-specific coefficient.

Example coefficients:

```text
Loam  → 0.85
Clay  → 1.10
Sandy → 0.65
```

Estimated water savings:

```text
Water Saved % = (1 − IR / 22) × 100
```

where `22 L/m²` represents the baseline used by the model for comparison.

> These formulas represent the project's implemented decision-support logic and should be calibrated against local agronomic measurements before being used for real-world irrigation decisions.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| UI | ShadCN, Framer Motion, Recharts |
| State Management | Zustand, TanStack React Query |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16, SQLAlchemy ORM |
| Authentication | JWT, PyJWT, bcrypt |
| Containerization | Docker, Docker Compose |
| Deployment | Vercel, Railway / Render |

---

## SDG Alignment

IrrigateWise contributes to the following **United Nations Sustainable Development Goals**:

- **SDG 2 – Zero Hunger:** Supports improved agricultural decision-making and crop guidance.
- **SDG 6 – Clean Water and Sanitation:** Promotes efficient irrigation and reduced water usage.
- **SDG 12 – Responsible Consumption and Production:** Encourages precision-based resource utilization.
- **SDG 13 – Climate Action:** Supports reduced agricultural water footprint.
- **SDG 15 – Life on Land:** Encourages soil health monitoring and sustainable land management.

---

## Data & Security

- Database credentials are stored through environment variables.
- Secret keys are not included in the repository.
- `.env` and `.env.local` files should remain excluded through `.gitignore`.
- Sample/seed data should contain only synthetic or non-sensitive information.
- Authentication uses JWT-based access control.
- Production deployments should use HTTPS and securely managed environment variables.

---

## Project Purpose

IrrigateWise aims to demonstrate how **soil data, computational decision-making, and modern web technologies** can be combined to build a practical smart irrigation platform for sustainable agriculture.

The platform is intended as a **decision-support and academic/project prototype** and should be validated with agricultural experts and field measurements before deployment in production farming environments.
