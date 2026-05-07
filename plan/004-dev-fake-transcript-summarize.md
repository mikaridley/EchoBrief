## Goal
Quickly verify the summarization output without uploading audio.

## Approach
- Add `POST /api/summarize` that accepts `{ "transcript": "..." }`
- Return the same structured shape as `/api/process` (via `ProcessResponse`)
- Add a tiny CLI script `backend/scripts/dev_summarize.py` for local quick runs

## Questions (answer before polishing UX)
- Do we want `/api/summarize` to be **dev-only** (disabled in prod), or always available?
- Should the endpoint return `language` (best-effort) or keep it `null` for now?

