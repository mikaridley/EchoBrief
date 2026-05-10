# EchoBrief

EchoBrief turns a meeting recording into a structured brief: **transcript**, **summary**, **participants** (when the text supports it), **decisions**, and **action items**, with optional **DOCX** export.

**Live demo:** [https://echo-brief-demo.vercel.app/](https://echo-brief-demo.vercel.app/)

**Demo uploads:** File upload is only available after the maintainer grants you access (allowlist / quota). If you need to try uploads on the hosted demo, contact the repository owner.

---

## What’s in the repo

| Part        | Stack                         | Role                                      |
| ----------- | ----------------------------- | ----------------------------------------- |
| `frontend/` | React 19, Vite 8, TypeScript  | Upload UI, Google sign-in, results        |
| `backend/`  | FastAPI, OpenAI (Whisper + chat) | Transcribe, summarize, auth, quotas, DOCX |

---

## Clone and run locally

### Prerequisites

- **Node.js** 20+ (for the frontend)
- **Python** 3.11+ and `pip` (for the backend)
- An **OpenAI API key** if you want real transcription and summarization (otherwise those steps need to stay disabled or mocked per your setup)

### 1. Clone

```bash
git clone <your-fork-or-upstream-url> EchoBrief
cd EchoBrief
```

### 2. Backend

```bash
cd backend
python -m venv .venv
```

Activate the venv (Windows PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate the venv (macOS / Linux):

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
```

Copy environment template and edit values (`Copy-Item .env.example .env` in PowerShell).

```bash
cp .env.example .env
```

**Fastest path (local dev, no Google / Mongo):** in `backend/.env` set:

- `ENV=local`
- `AUTH_ENABLED=0`
- `OPENAI_API_KEY=...` (if you use real AI calls)

The API will treat you as a local dev user when auth is off (only allowed with `ENV=local`).

**Full auth (matches production-style):** set `AUTH_ENABLED=1`, `GOOGLE_CLIENT_ID`, and `MONGO_URI` as in `.env.example`, then ensure your Google user exists in your allowlist / DB as your app expects.

Start the API from the `backend` directory (default port **8000** matches the frontend default):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env   # or: Copy-Item .env.example .env
```

Edit `frontend/.env`:

- `VITE_API_BASE_URL` — same origin/port as the API (e.g. `http://localhost:8000`)
- `VITE_GOOGLE_CLIENT_ID` — required when the backend has `AUTH_ENABLED=1` and you use Google sign-in; for local auth-off backend you can still set a placeholder or your real client ID for UI testing

For Google OAuth, create a **Web** OAuth client and add **Authorized JavaScript origins** such as `http://localhost:5173`. If Google returns `400 invalid_request`, check client type, origins, consent screen test users, and that `VITE_GOOGLE_CLIENT_ID` is set.

Run the dev server:

```bash
npm run dev
```

Open the URL Vite prints (usually [http://localhost:5173](http://localhost:5173)).

### Useful commands

| Where       | Command                                              | Purpose                                                |
| ----------- | ---------------------------------------------------- | ------------------------------------------------------ |
| `frontend/` | `npm run build`                                      | Production build (output in `dist/`)                   |
| `frontend/` | `npm run lint`                                       | ESLint                                                 |
| `backend/`  | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | Typical production-style start (e.g. on Render)        |

---

## Configuration reference

- **Frontend env:** [`frontend/.env.example`](frontend/.env.example)
- **Backend env:** [`backend/.env.example`](backend/.env.example)

Never commit real `.env` files or API keys. The repo should rely on examples plus host-specific secrets (Vercel / Render / Atlas).

---

## Architecture notes (short)

- The browser obtains a **Google ID token** and, in the current demo-oriented flow, stores it in **`sessionStorage`** and sends it as **`Authorization: Bearer`** to the API. The API verifies the token when `AUTH_ENABLED=1`.
- For production hardening, a common next step is a **server session** in an **`HttpOnly` cookie** after a one-time token exchange; that is tracked in the backlog in [`PROCESS.md`](PROCESS.md).

---

## Contributing / learning

- Numbered phase plans live under [`plan/`](plan/) (ordering described in [`plan/the-process-for-me.md`](plan/the-process-for-me.md) if present). Use them if you extend the pipeline (e.g. diarization, exports, observability).
- If something in this README drifts from the code, trust the repo and `.env.example` files first, then update the README in the same PR.
