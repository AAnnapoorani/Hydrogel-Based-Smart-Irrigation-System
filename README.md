# IrrigateWise – Smart Irrigation Platform

📍 Built for Erumaiyur Village, Tambaram, Tamil Nadu  
🌾 Soil Analysis · Crop Recommendation · Water Optimization

---

## Folder Structure

```
irrigatewise/
├── docker-compose.yml
├── seed.sql
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env
│   ├── main.py          ← FastAPI app + all routes
│   ├── models.py        ← SQLAlchemy ORM models
│   ├── schemas.py       ← Pydantic request/response models
│   ├── logic.py         ← Soil scoring + irrigation formula
│   └── database.py      ← DB connection & session
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.js
    ├── next.config.js
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx             ← Landing page
        │   ├── dashboard/page.tsx   ← Dashboard
        │   ├── soil/page.tsx        ← Soil Analysis
        │   ├── irrigation/page.tsx  ← Irrigation Optimizer
        │   └── reports/page.tsx     ← Reports
        ├── components/
        │   ├── Navbar.tsx
        │   ├── StatCard.tsx
        │   └── WeatherWidget.tsx
        └── lib/
            └── api.ts               ← Axios client
```

---

## Environment Variables

### backend/.env
```env
DATABASE_URL=postgresql://irrigate_user:irrigate_pass@db:5432/irrigatewise
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30
```

### frontend/.env.local
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Local Development

### Prerequisites
- Docker + Docker Compose  
- Node.js 20+  
- Python 3.12+

### Option 1: Docker (Recommended)

```bash
# Clone and start everything
git clone https://github.com/your-org/irrigatewise
cd irrigatewise
docker-compose up --build

# Seed sample data (after containers start)
docker exec -it irrigatewise-db-1 psql -U irrigate_user -d irrigatewise -f /seed.sql
```

Open: http://localhost:3000

### Option 2: Manual

**Backend:**
```bash
cd C:\Users\ANNAPOORANI\Downloads\irrigatewise-fullstack 1\irrigatewise\backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL separately, then:
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd C:\Users\ANNAPOORANI\Downloads\irrigatewise-fullstack 1\irrigatewise\frontend
npm install
npm install leaflet react-leaflet
npm run dev          # http://localhost:3000
```

---

## API Reference

| Method | Endpoint               | Auth | Description                |
|--------|------------------------|------|----------------------------|
| POST   | /register              | No   | Register new user          |
| POST   | /login                 | No   | Login, returns JWT         |
| POST   | /soil/analyze          | Yes  | Analyze soil parameters    |
| GET    | /soil/history          | Yes  | Get soil analysis history  |
| POST   | /irrigation/calculate  | Yes  | Calculate irrigation needs |
| POST   | /irrigation/schedule   | Yes  | Schedule irrigation        |
| GET    | /irrigation/history    | Yes  | Get irrigation history     |
| GET    | /reports               | Yes  | Combined reports data      |
| GET    | /reports/export        | Yes  | Export PDF (download URL)  |
| GET    | /health                | No   | Health check               |

Interactive docs: http://localhost:8000/docs

---

## Production Deployment

### Vercel (Frontend) + Railway (Backend + DB)

**Backend on Railway:**
1. Create new Railway project → Add PostgreSQL service
2. Add Python service → connect GitHub repo (backend/ folder)
3. Set env vars: DATABASE_URL (from Railway PostgreSQL), SECRET_KEY
4. Deploy → copy the Railway public URL

**Frontend on Vercel:**
1. Connect GitHub repo to Vercel → set Root Directory: `frontend`
2. Add env var: `NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app`
3. Deploy

### Alternative: Render
- Backend: New Web Service → Docker → Root: `/backend`
- Database: New PostgreSQL → copy Internal URL → set as DATABASE_URL
- Frontend: New Static Site → build command: `npm run build`, publish: `.next`

---

## Key Formulas

### Soil Fertility Score
```
score = N_score×0.30 + P_score×0.20 + K_score×0.20 + pH_score×0.15 + OC_score×0.15
Classification: ≥70 → High | 45–69 → Medium | <45 → Low
```

### Irrigation Requirement
```
SMD = SM_optimal − SM_current
IR  = α × SMD          (α = soil coefficient; loam=0.85, clay=1.1, sandy=0.65)
Water Saved % = (1 − IR/22) × 100   (22 L/m² = traditional baseline)
```

---

## Tech Stack

| Layer     | Technology                           |
|-----------|--------------------------------------|
| Frontend  | Next.js 14, TypeScript, Tailwind CSS |
| UI        | ShadCN, Framer Motion, Recharts      |
| State     | Zustand + React Query (TanStack)     |
| Backend   | FastAPI (Python 3.12)                |
| Database  | PostgreSQL 16 + SQLAlchemy ORM       |
| Auth      | JWT (PyJWT + bcrypt)                 |
| Deploy    | Docker, Vercel, Railway/Render       |

---

## SDG Alignment
- **SDG 2** Zero Hunger – Improved crop yield guidance
- **SDG 6** Clean Water – 25–35% water savings
- **SDG 12** Responsible Consumption – Precision resource use
- **SDG 13** Climate Action – Lower agricultural water footprint
- **SDG 15** Life on Land – Soil health monitoring
