# PROCESS.md — EchoBrief (Audio → Transcript → Summary)

## What this project does
EchoBrief is a small web app where a user uploads a meeting recording and gets back:
- **Transcript**
- **Structured summary** (summary / participants / decisions / action items)
- **DOCX export**

## What’s implemented right now (repo-truth)
- **Frontend**: `frontend/` (Vite + React)
  - Config via env:
    - `VITE_API_BASE_URL` (backend URL)
    - `VITE_GOOGLE_CLIENT_ID` (Google OAuth)
- **Backend**: `backend/` (FastAPI)
  - Routes (all under `/api`):
    - `GET /health`
    - `POST /process` (audio upload pipeline)
    - `POST /summarize` (text-only summarization,)
    - `POST /docx` (generate Word file)
    - `POST /auth/*` (Google token verification + user/quota checks)
  - Cost controls:
    - On-disk cache for summaries (`backend/.cache/summaries`)
    - Optional local dev rate limit (in-memory)
    - Mongo-backed quota (requires `AUTH_ENABLED=1`)

## Current architecture (high level)
1) **Frontend** uploads audio → backend `POST /api/process`
2) Backend transcribes (Whisper) → gets transcript text
3) Backend summarizes transcript (LLM - OpenAI) → strict JSON
4) Backend returns structured JSON to frontend
5) Frontend can request a Word export via `POST /api/docx`

## API contract (simplified)
The backend response is a `ProcessResponse`-shaped JSON object with:
- `transcript: string`
- `summary: string`
- `participants: string[]`
- `decisions: string[]`
- `action_items: { task: string, owner: string|null, due: string|null }[]`
- `language: string|null`
- `meta: object` (best-effort timings, model names, cache flags)

## How AI was used (what mattered)
- **Prompt design**: forced **JSON-only**, no extra keys, and strict anti-hallucination rules.
- **Validation**: server rejects malformed/extra-key JSON and can optionally do a single “fix JSON” retry.
- **Cost discipline**: cache-by-transcript-hash ensures the same transcript does not re-spend tokens during dev.

## Known limitations / non-goals (for this assignment)
- No true speaker diarization (Whisper transcript is plain text; participants are best-effort inference).
- No permanent storage of uploaded audio (temporary processing only).

## Delivery checklist (keep this current)
- [ ] Repo builds and runs locally (frontend + backend)
- [ ] `.env.example` exists; `.env` is not committed
- [ ] Deployment steps documented (Vercel + Render + Atlas)
- [ ] Smoke test: upload audio → get transcript + summary → export docx