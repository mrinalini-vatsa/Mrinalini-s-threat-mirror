# Mrinalini's ThreatMirror: Autonomous Security Investigation & SOC Platform

Production-grade full-stack SOC investigation platform with autonomous alert generation, enrichment, decisioning, correlation, and explainable incident reporting.

## Architecture

- Backend: FastAPI + async endpoints + SQLAlchemy ORM + Alembic
- Database: PostgreSQL (Neon-compatible)
- Frontend: React + Vite dashboard
- Deploy: Backend on Render, Frontend on Vercel

## Backend Features

- Autonomous alert generation every 60 seconds (`alert_worker`)
- Enrichment engine (AbuseIPDB + optional VirusTotal)
- Rule-based decision engine with confidence and reason trace
- Incident lifecycle timeline (`NEW`, `ENRICHED`, `ANALYZED`, `RESOLVED`)
- Correlation engine linking repeated IP alerts
- Observability via logs and metrics API
- Gemini-based incident report generation endpoint

## System Design Highlights

- Asynchronous alert processing pipeline
- Rule-based decision engine with explainability
- Correlation engine for detecting repeated threats
- Observability via metrics and logging

## Project Structure

```text
backend/
  app/
    api/
    models/
    schemas/
    services/
    core/
    workers/
    utils/
  alembic/
    versions/
frontend/
  src/
```

## Database Schema

Tables:

- `alerts`
- `enrichments`
- `decisions`
- `alert_states`
- `correlations`

Migration included at `backend/alembic/versions/0001_initial_schema.py`.

## Local Setup

### 1) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
```

Update `.env` with real values:

- `DATABASE_URL`
- `ABUSEIPDB_API_KEY`
- `VIRUSTOTAL_API_KEY`
- `GEMINI_API_KEY`

Run migrations:

```bash
alembic upgrade head
```

Run API:

```bash
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

Set `VITE_API_BASE_URL=http://localhost:8000`.

Run:

```bash
npm run dev
```

## API Routes

- `GET /api/health`
- `GET /api/alerts`
- `GET /api/alerts/{alert_id}`
- `GET /api/metrics`
- `GET /api/alerts/{alert_id}/report`
- `POST /api/alerts/{alert_id}/resolve`

## Deployment

## Deploy Backend to Render

1. Push repo to Git provider.
2. Create new Render Web Service.
3. Root directory: `backend`.
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add env vars:
   - `DATABASE_URL`
   - `ABUSEIPDB_API_KEY`
   - `VIRUSTOTAL_API_KEY`
   - `GEMINI_API_KEY`
7. Run DB migration once from Render shell:
   - `alembic upgrade head`

## Deploy Frontend to Vercel

1. Import project in Vercel.
2. Set root directory to `frontend`.
3. Framework preset: `Vite`.
4. Build command: `npm run build`
5. Output directory: `dist`
6. Add env var:
   - `VITE_API_BASE_URL=https://<your-render-domain>`
7. Deploy.

## Notes

- No secrets are hardcoded.
- Alert worker starts automatically with FastAPI lifespan.
- In production, consider adding Redis/queue for horizontal worker scaling.

## Limitations & Future Improvements

- Replace in-process worker with Celery + Redis
- Add distributed caching (Redis)
- Implement rate limit handling for APIs
- Add authentication layer
