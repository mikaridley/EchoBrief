# Deploy step-by-step (Vercel + Render + MongoDB Atlas)

## Assumptions (repo truth)
- Frontend: `frontend/` (Vite + React)
- Backend: `backend/` (FastAPI) entrypoint `app.main:app`
- Backend routes are under `/api` (health is `/api/health`)
- Auth in prod requires:
  - `AUTH_ENABLED=1`
  - `MONGO_URI`
  - `GOOGLE_CLIENT_ID`

## Step 0 — Prep (local)
- Ensure secrets are **not** committed:
  - `.env` files should be gitignored
- Make sure backend has `requirements.txt`
- Make sure frontend builds locally:
  - `npm run build` creates `frontend/dist`

## Step 1 — Create MongoDB Atlas DB
- Create a cluster (free is fine for MVP)
- Create a DB user/password
- Network access:
  - For MVP: allow `0.0.0.0/0` (then lock down later)
- Copy the connection string and save it for Render as:
  - `MONGO_URI`
- Pick DB name (or use default):
  - `MONGO_DB_NAME=echobrief`

## Step 2 — Deploy backend to Render (FastAPI)
- Create a new **Web Service**
- Connect your GitHub repo
- Settings:
  - Root directory: `backend`
  - Build command: `pip install -r requirements.txt`
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables (Render → Environment):
  - `ENV=prod`
  - `OPENAI_API_KEY=...`
  - `AUTH_ENABLED=1`
  - `GOOGLE_CLIENT_ID=...`
  - `MONGO_URI=...`
  - `MONGO_DB_NAME=echobrief`
  - `CORS_ORIGINS=https://<your-vercel-domain>`
- Deploy and copy the backend URL (you’ll use it in Vercel)

## Step 3 — Deploy frontend to Vercel (Vite SPA)
- Create a new Project from your GitHub repo
- Settings:
  - Root directory: `frontend`
  - Build command: `npm ci && npm run build`
  - Output directory: `dist`
- Environment variables (Vercel → Project → Settings → Env Vars):
  - `VITE_API_BASE_URL=https://<your-render-backend-domain>`
  - `VITE_GOOGLE_CLIENT_ID=...` (same as backend)
- Deploy and copy the frontend URL

## Step 4 — Lock CORS to the frontend domain
- Update Render env var:
  - `CORS_ORIGINS=https://<your-vercel-domain>`
- Redeploy backend
- Verify browser requests succeed (no CORS errors)

## Step 5 — Smoke test (prod)
- Backend:
  - Open `/api/health` and confirm 200 OK
- Frontend:
  - Login (Google)
  - Upload audio → get transcript+summary
  - Export DOCX

## Common gotchas
- If backend returns `AUTH_DISABLED`, you’re running with `AUTH_ENABLED=0` in prod (not allowed).
- If backend crashes on startup with `AUTH_ENABLED=1 requires MONGO_URI` / `GOOGLE_CLIENT_ID`, set those env vars on Render.
- If browser shows CORS errors, fix `CORS_ORIGINS` to exactly match the Vercel domain (scheme + host).

## Questions to confirm (so we can make this “copy/paste exact”)
- Are you deploying exactly on **Vercel + Render + Atlas**, or a different host?
- Do you want to keep Atlas open to `0.0.0.0/0` for MVP, or lock it down now?

