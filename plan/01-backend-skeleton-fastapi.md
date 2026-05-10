# Backend skeleton (FastAPI)

## Decisions (based on our chat)
- **Python**: 3.12 (latest stable → best performance/features; 3.11 only if a dependency lags)
- **Deps**: start with `requirements.txt` (lowest friction); can migrate to Poetry later
- **CORS**: allow both `http://localhost:5173` and `http://localhost:3000` for local dev
- **Uploads**: save to **temporary disk file** (streaming) and delete after processing

## Why Python 3.12 (vs 3.11)
- **Pick 3.12** when you control the runtime: better speed, modern typing, longer runway before upgrades.
- **Pick 3.11** only if you hit dependency incompatibility or a platform constraint (rare nowadays).

## What Poetry is (simple explanation)
Poetry is a Python tool that:
- installs dependencies,
- locks exact versions (`poetry.lock`) so installs are reproducible,
- manages virtualenvs,
- uses a single `pyproject.toml` instead of `requirements.txt`.

**Trade-off**:
- Poetry = more structure and reproducibility
- `requirements.txt` = simpler to learn and easier for beginners / small projects

## Backend structure we’ll create
```
backend/
  app/
    main.py
    api/routes/{health.py,process.py,docx.py}
    core/config.py
    schemas/meeting.py
    services/docx.py
  requirements.txt
  .env.example
```

## MVP endpoints
- `GET /api/health` → `{ "ok": true }`
- `POST /api/process` (multipart `file`) → mocked JSON in our contract
- `POST /api/docx` (JSON body) → returns a `.docx` download

## Notes / best practices we follow
- Thin route handlers (HTTP layer) + services (logic) + schemas (contracts)
- Env-driven settings (CORS origins, upload size limit)
- Don’t load huge uploads into RAM; stream to disk and clean up

