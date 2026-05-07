# PROCESS.md — Meeting Summarizer (Whisper + LLM)  

## Goal
Build a web app where a user uploads an `mp3/wav` meeting recording and the system returns:
- **Full transcription**
- **Meeting summary**
- **Participants list** (if can be inferred)
- **Decisions made**
- **Action items**
- **Option to download as a Word file**

Tech constraints (per assignment): **React frontend**, **Python backend**, **Whisper API** for transcription, and **Claude API or any other LLM** for summarization/structuring. Output should be shown in a **clean UI**.

---

## Target repo structure (as requested)

```
meeting-summarizer/
├── backend/
│   ├── main.py
│   ├── services/
│   │   ├── transcribe.py
│   │   └── summarize.py
│   ├── requirements.txt
│   └── .env  # do NOT commit
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── api.js
│   └── package.json
├── .PROCESS
└── README.md
```

---

## Product scope (MVP)
- **Upload**: single audio file (`.mp3`, `.wav`) from browser.
- **Backend pipeline**:
  1) Validate file → store temporarily  
  2) Send to Whisper → get transcript (text)  
  3) Send transcript to LLM → get structured JSON output  
  4) Return JSON to frontend  
  5) .doGenerate `cx` (Word) from structured output (download endpoint)
- **Frontend**:
  - Upload button + progress indicator
  - Display transcript (collapsible/scrollable)
  - Display summary sections (Summary / Participants / Decisions / Action Items)
  - “Download Word” button

Non-goals for MVP (can add later):
- Speaker diarization with timestamps
- Multi-language UI
- Authentication / user accounts
- Persistent storage of uploads/results

---

## Architecture & data contracts

### Backend endpoints (FastAPI)
- **POST** `/api/process`
  - **Input**: `multipart/form-data` with `file`
  - **Output** (JSON):
    - `transcript`: string
    - `summary`: string (high-level)
    - `participants`: string[] (or empty)
    - `decisions`: string[]
    - `action_items`: array of `{ owner?: string, task: string, due?: string }`
    - `language`: string (best-effort)
    - `meta`: `{ duration_sec?: number, model_versions?: {...} }` (optional)

- **POST** `/api/docx`
  - **Input**: JSON payload in the same shape as `/api/process` output (or a `result_id` if we later persist)
  - **Output**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (file download)

### Frontend API wrapper
- `uploadAndProcess(file)` → calls `/api/process`
- `downloadDocx(result)` → calls `/api/docx`

---

## Implementation plan (step-by-step)

### Phase 0 — Repo scaffolding
- Create `meeting-summarizer/` root and the requested folders/files.
- Add `.gitignore` covering `backend/.env`, audio uploads, `.venv`, `node_modules`, build artifacts.
- Add `README.md` with local run instructions (frontend + backend).

### Phase 1 — Backend skeleton (FastAPI)
- Implement `backend/main.py` with:
  - CORS for local dev (`http://localhost:5173` or `3000`)
  - `/api/health`
  - `/api/process` (stub returns mocked JSON)
  - `/api/docx` (stub returns basic docx)

### Phase 2 — Transcription service (Whisper)
- Implement `backend/services/transcribe.py`:
  - Accept file path/bytes
  - Call Whisper API (OpenAI or other provider allowed)
  - Return transcript string + detected language if available
  - Handle common failures: file too large, unsupported format, API timeouts

### Phase 3 — Summarization service (LLM)
- Implement `backend/services/summarize.py`:
  - Input: transcript text
  - Output: strict JSON in the contract above
  - Add robust parsing/validation:
    - JSON schema validation (pydantic)
    - Retry once with “fix JSON” prompt if malformed

### Phase 4 — Word export
- Generate `.docx` using a Python library (e.g., `python-docx`)
- Include sections:
  - Summary
  - Participants
  - Decisions
  - Action Items (bullets/table)
  - Transcript (optional; maybe appended/collapsible choice in UI)

### Phase 5 — Frontend (React)
- `App.jsx`:
  - file picker
  - submit button
  - loading/progress
  - render results
- `components/UploadButton.jsx`, `components/SummaryDisplay.jsx` (or similar)
- `api.js` for backend calls

### Phase 6 — Polish + handoff
- Better UI states: empty/error/success
- Large transcript UX (collapse + copy button)
- README finalization + run instructions
- Final pass: ensure `PROCESS.md` answers the assignment explicitly

---

## System Prompt (LLM summarizer) — draft

This will be refined after we see real transcripts.

### System prompt (candidate)
- You are a meeting analyst. Given a transcript, produce **ONLY valid JSON** matching the schema.
- Extract **participants** only if clearly stated or strongly implied; otherwise return `[]`.
- “Decisions” should be concrete and phrased as outcomes.
- “Action items” must be tasks that someone should do; include owner/due only if present.
- If transcript is noisy/partial, be transparent in phrasing and avoid fabrications.

### JSON schema (conceptual)
```json
{
  "summary": "string",
  "participants": ["string"],
  "decisions": ["string"],
  "action_items": [
    { "task": "string", "owner": "string?", "due": "string?" }
  ]
}
```

### Why this prompt structure
- Enforcing “JSON only” + schema reduces UI glue code and parsing failures.
- Explicit anti-hallucination rules protect correctness when transcripts are messy.
- Separating decisions vs action items improves downstream display and Word export.

---

## How I’ll use AI during development (to document)
I will document concrete uses here as we build:
- **Prompt iteration**: create/compare system prompts on real sample transcripts.
- **Edge cases**: ask AI to propose failure modes (bad audio, long transcript, mixed languages) and mitigation.
- **Code assistance**: generate boilerplate for FastAPI endpoints, React components, and docx templates, then adapt to project conventions.
- **Debugging**: interpret API errors and propose fixes (timeouts, payload format).

When I use AI, I’ll paste:
- The exact prompt(s)
- What I changed in the code based on the output
- What I rejected and why

---

## Blockers & resolutions log (fill during work)
Add entries as they happen.

### Template
- **Date/Time**
- **Issue**
- **Symptom / error**
- **Root cause**
- **Fix**
- **What I learned / prevention**

---

## Time tracking (fill during work)
Assignment asks “how long it took in practice”.

- **Scaffolding**: 0:00
- **Backend**: 0:00
- **Whisper integration**: 0:00
- **LLM summarization**: 0:00
- **Word export**: 0:00
- **Frontend**: 0:00
- **Polish + docs**: 0:00

---

## Delivery checklist (matches assignment)
- [ ] GitHub repo link with working code
- [ ] Local run instructions or live demo
- [ ] `PROCESS.md` describing:
  - [ ] how I planned before coding
  - [ ] how I used AI (prompt examples)
  - [ ] where I got stuck + how resolved
  - [ ] full system prompt + explanation why it’s built that way
- [ ] App outputs:
  - [ ] transcript
  - [ ] summary
  - [ ] participants (if possible)
  - [ ] decisions
  - [ ] action items
  - [ ] Word download

<!-- my insights(do no remove) -->

<!-- first i reseraches what is the best practices, best folder structure and best technologies in prder to make each step. -->
<!-- secondly i wrote clearly the pipeline so i know what i need to do step after step in order to make the best result and acording to MVP method -->
<!-- pipeline - 
1) User uploads file 
2) Backend stores locally/temporarily 
3) Sent to Whisper API for transcription 
4) Text passed to LLM with a structured System Prompt 
5) Processed JSON returned to Frontend  -->