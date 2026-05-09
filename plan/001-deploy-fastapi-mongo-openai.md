# Deploy plan — FastAPI + MongoDB Atlas + OpenAI

## Goal
Deploy the project so:
- Frontend is served fast via CDN (static hosting)
- Backend (FastAPI) runs as a web service
- MongoDB is managed (no self-hosting)
- Secrets (OpenAI key, Mongo URI) are stored as environment variables (never in git)

## Recommended setup (best default)
- **Frontend**: Vercel (Static / SPA)
- **Backend**: Render (Web Service)
- **Database**: MongoDB Atlas

Why I pick this over “everything in one place”:
- Vercel is usually the smoothest + fastest for React static hosting (CDN, previews)
- Render is beginner-friendly for FastAPI, env vars, logs, and redeploys
- Atlas is the standard managed Mongo choice

Trade-offs vs alternatives:
- One platform (Render for both FE+BE): simpler, but FE CDN/preview UX is usually weaker than Vercel
- Fly.io for backend: more control/performance, but more ops learning

## Assumptions I’m making (so the steps are concrete)
- Frontend is a Vite SPA and talks to backend via an API base URL
- Backend runs with Uvicorn from `backend/app/main.py` (`app.main:app`)
- Mongo is accessed via a connection string (Atlas URI)
- OpenAI calls happen only from backend (good: keys stay server-side)

## Status (repo truth)
- Backend entrypoint is: `backend/app/main.py`
- Mongo driver is: Motor (`motor.motor_asyncio.AsyncIOMotorClient`)
- Frontend build output is: Vite `dist/`
- Uploads are processed temporarily (no permanent storage)

## Execution steps

### Step A — MongoDB Atlas (DB)
- Create a free/paid cluster
- Create a DB user + allowlist Render outbound IPs (or allow all for MVP, then lock down)
- Save the connection string as `MONGO_URI` (this repo’s env var name)

### Step B — Backend on Render
- Create a **Web Service** from the repo
- Root directory: `backend`
- Build command:
  - `pip install -r requirements.txt`
- Start command (example):
  - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add env vars:
  - `OPENAI_API_KEY`
  - `MONGO_URI`
  - `MONGO_DB_NAME` (default: `echobrief`)
  - `ENV=prod`
  - `CORS_ORIGINS=https://<your-vercel-domain>`
  - `AUTH_ENABLED=1` (recommended in production)
  - `GOOGLE_CLIENT_ID` (required if auth is enabled)
  - Any other config used by the app (model name, limits, etc.)
- Ensure CORS allows the Vercel domain (and local dev if needed)

### Step C — Frontend on Vercel
- Import repo in Vercel
- Root directory: `frontend`
- Build command: `npm ci && npm run build` (or Vercel default)
- Output: `dist`
- Add env var:
  - `VITE_API_BASE_URL` = your Render backend URL (example: `https://your-api.onrender.com`)
  - `VITE_GOOGLE_CLIENT_ID` = same Google OAuth client id you use in the backend
- (If SPA) Add rewrite so all routes go to `index.html`

### Step D — Smoke test
- Call backend `/api/health` (or equivalent)
- Upload an audio file → verify response
- Confirm DB writes/reads (if implemented)
- Confirm OpenAI calls succeed from production

## Rollback & safety
- Never commit `.env`
- Rotate `OPENAI_API_KEY` if it was ever leaked
- Add basic rate limiting and file size limits if public

