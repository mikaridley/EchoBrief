# Development process — EchoBrief

## What the system does
**EchoBrief** is a small web app: the user uploads a meeting recording and, in order, gets:

1. **Full transcript** of the recording  
2. **Meeting summary**  
3. **Participant list** (when the audio/transcript allows identifying them — best-effort, not true diarization unless you add it later)  
4. **Decisions** that were made in the meeting  
5. **Action items** (tasks to follow up on)  

Optionally, the same content can be exported as **DOCX**.

**Frontend:** React + Vite + TypeScript.
 **Backend:** FastAPI with OpenAI (transcription + summarization). Google sign-in and MongoDB-backed quotas protect paid API usage in production; they are optional for local development.

---

## 1. How I planned the system before coding

### How I started
First I researched **best practices**, a **folder structure** that would stay maintainable, and the **right technologies for each step**—in a deliberate order so each choice supported the next.

Then I wrote the **pipeline** down clearly, step by step, so I always knew what to build next and could stay close to an **MVP**: ship a thin vertical slice that works end-to-end before polishing edge cases.

### Target pipeline (MVP)
1. User uploads a file  
2. Backend stores it **locally and temporarily**  
3. Audio is sent to the **Whisper** API for transcription  
4. Transcript text is passed to an **LLM** with a **structured system-style prompt**  
5. **Processed JSON** is returned to the frontend  

From there I split the work into layers and phases:

*Layer:* User flow  
*What I planned:* Upload → loading → **full transcript** → **summary** → **participants** (if identifiable) → **decisions** → **action items** → Word download

*Layer:* API contract  
*What I planned:* One stable response shape (`ProcessResponse`) so the frontend does not break when the implementation changes

*Layer:* Safety and cost  
*What I planned:* Max upload size, secrets only in env, on-disk summary cache keyed by transcript hash (fewer repeat paid calls in dev)

*Layer:* Auth  
*What I planned:* Google OAuth on the client, JWT verification on the server + per-user summary quota

**Why this structure?**  
Splitting into routes / services / schemas makes testing easier, makes it possible to swap providers later, and lets you change prompts without touching HTTP wiring.

---

## 2. How I used AI during development

### 2.1 Cursor / coding assistant (example prompts)
Prompt Examples:
1. **Frontend skeleton**  
   "Role: Expert React & Frontend Architect

   Task: Initialize a React frontend using Vite and set up a specific, modular folder architecture.

   Core Technology Stack:

   Framework: React (Vite)
   Styling: Modular CSS (following the provided directory structure)> Directory Structure Requirements: Create the following folder hierarchy exactly as specified. Ensure empty directories contain a .gitkeep if necessary to maintain the structure.
   In main.css, import all files from setup/, basics/, cmps/, and pages/ to ensure a single source of truth for styles.
      src/
      ├── assets/
      │   ├── fonts/
      │   ├── imgs/
      │   └── styles/
      │       ├── basics/
      │       │   ├── base.css
      │       │   └── layout.css
      │       ├── cmps/
      │       ├── pages/
      │       ├── setup/
      │       │   ├── _mq.css
      │       │   ├── _typography.css
      │       │   └── _variables.css
      │       └── main.css
      ├── cmps/
      ├── config/
      ├── pages/
      ├── services/
      ├── utils/
      ├── index.jsx
      └── RootCmp.jsx
      "

2. **Data-to-UI Mapping Specification**  
   "Role: Expert Frontend Developer and UI/UX Designer.

   Task: Transform a JSON data object into a clean, modern, and interactive user interface. You must map specific data fields to the following UI components while maintaining a professional aesthetic:

   Summary (Priority 1): Display the summary data at the very top of the page. It should be formatted as a high-readability paragraph to serve as the executive overview.

   Transcript (Collapsible): Create a section titled "Transcript." This must be a collapsible accordion that is closed by default. Include a chevron/arrow icon that points up when closed and rotates when clicked to reveal the full text.

   Participants (Visual Icons): Map the participants data to a horizontal row of rounded avatar divs:
   Each div should contain a person icon.
   Assign a unique, distinct background color to each participant.
   Implement a hover state/tooltip that displays the participant’s full name.

   Decisions: List all items from the decisions field as a clean bulleted list under a clear "Decisions" heading.

   Action Items (Ownership): List items from the action_items field as bullets. For each item, append a small rounded icon at the end of the line representing the "Owner" of that task, matching the color coding used in the Participants section."

3. **Deployment recommendation**  
  "Role: Cloud Infrastructure Architect and Senior DevOps Engineer.

  Task: Recommend the most efficient, cost-effective, and reliable deployment strategy for a Full Stack "take-home" assignment. The solution must prioritize speed of setup and handle specific technical constraints without the overhead of complex enterprise providers (AWS/GCP/Azure).

  Project Specifications:
  -Backend: Python (FastAPI). Critical Requirement: Must support long-running requests for OpenAI/Whisper processing without triggering 504 Gateway Timeouts.
  -Frontend: React (Vite).
  -Database: MongoDB Atlas (Cloud-hosted).
  -Security: Requires secure Environment Variable management for OpenAI API keys.

  Evaluation Criteria:
  -Deployment Velocity: Must be deployable within a 2-hour window.
  -Cost Efficiency: Priority for Free Tier or "Pay-as-you-go" hobby tiers.
  -Simplicity: Prefer Platform-as-a-Service (PaaS) solutions over manual VPS or Kubernetes management.
  -Reliability: The architecture must ensure the connection stays open or provide a workaround (like background tasks) for AI processing times.
  "

### 2.2 LLM system prompt for meeting summary (full template + why)
The backend builds one user message per request in `summarize.py` (`_make_prompt`). The model sees this text (placeholders: **`TRANSCRIPT_LANGUAGE`** is inferred from the transcript, e.g. English or Spanish; the real **`### Transcript`** block ends with the full transcript text). Full prompt template:

```
### Role
You are an expert Executive Assistant and Meeting Analyst. Your goal is to extract high-value insights from meeting transcripts with 100% accuracy.

### Task
Analyze the provided transcript and return a structured summary, participants, decisions, and action items.

### Language
The transcript language is: TRANSCRIPT_LANGUAGE.
You MUST write ALL JSON string values in TRANSCRIPT_LANGUAGE. Do NOT translate to any other language.

### Output Format (STRICT)
Output ONLY a valid JSON object and nothing else.
Do NOT include conversational text.
Do NOT use markdown or code fences (do NOT wrap the answer in a fenced json block).
Do NOT add any extra top-level keys or nested keys beyond the schema.

Schema (EXACT):
{
  "summary": string,
  "participants": string[],
  "decisions": string[],
  "action_items": [{"task": string, "owner": string|null, "due": string|null}]
}

### Speaker Identification
First, estimate how many distinct people ACTIVELY SPEAK in the transcript (using conversational cues like turn-taking, "I" vs "you", first-person statements, agreements, questions, etc.).
Then label each active speaker:
- Use a real name ONLY when the speaker is self-introduced (e.g. "Hi, I'm Tom") OR strongly implied by context (e.g. directly addressed by name and they reply, or clearly the narrator/host of the recording).
- Otherwise use placeholders in first-speak order: "Speaker 1", "Speaker 2", "Speaker 3", ...
If the transcript has any content, "participants" MUST contain at least one item (there is always at least one speaker).

### Participant Filtering (CRITICAL)
STRICT RULE: A participant is ONLY someone who has spoken lines in the transcript. If a person is mentioned as "absent", "missing", or is discussed in the third person (e.g., "Frank is not here"), DO NOT include them in the participants list.
"participants" must include ONLY people who actively speak in the transcript.
Do NOT include third parties that are only mentioned, referred to in third person, or teams/companies/departments.
Example: if the narrator says "my brother Tom attends every meeting", Tom is NOT a participant unless Tom himself speaks in the transcript.

### Decisions
"decisions" must include only decisions explicitly made in the transcript. Otherwise return [].

### Action Items (Ownership)
"owner" is whoever must **perform** the task (the doer), not someone who is only mentioned as the target of contact.
- CRITICAL: If the task is phrased like "talk to Dan", "call Sarah", "email the vendor", "ping the manager", the **mission** is for someone else to reach out. The owner is the person who must do that outreach (e.g. the speaker who said "I will", or whoever was assigned in the same exchange), NOT Dan/Sarah/the vendor unless the transcript clearly assigns the work to them.
- Example: "I'll talk to Dan about the assets" → owner is the speaker (use their name from context or a matching "Speaker N" from participants), NOT "Dan".
- The owner MAY be an active participant from "participants" when they are the one who must act.
- The owner MAY be a third-party person or role only when the transcript clearly assigns **that** person or role to **do** the work (e.g. "Rich keeps the paper out there" → "Rich"; "the production manager will fix it" → "the production manager").
- NEVER invent a name or role that is not present or strongly implied in the transcript.
- If the doer cannot be identified, set "owner": null (never use the contact-only person as owner for "talk to X" tasks).
- If no due date is explicitly stated, set "due": null.

### Integrity checks (MUST satisfy)
- "participants" contains only people with spoken lines in the transcript (not absent/missing/mentioned-only).
- Every action_items[].owner is either null OR the person/role who must **perform** the task; never use someone who is only the object of "talk to / call / email" unless they are clearly assigned to do the work.
- Output JSON matches the schema exactly, with no extra keys.

### Transcript
<full transcript text is appended here by the server>
```

#### Why it is built this way
| Choice | Reason |
|--------|--------|
| **JSON-only, fixed schema** | Matches `ProcessResponse` / Pydantic on the server: easy to validate, cache, and render in the UI or DOCX without fragile prose parsing. |
| **No markdown / no extra keys** | Stops the model from wrapping output in fenced code blocks or adding fields that would break strict parsing. |
| **Language block** | Summaries stay in the same language as the meeting so the UI does not flip languages by accident. |
| **Speaker rules + participant filtering** | Whisper gives plain text, not diarization; explicit rules reduce “ghost” participants and people who are only mentioned but never speak. |
| **Action owner = doer** | Avoids a common bug: setting owner to “Dan” for “I will call Dan” when the assignee is the speaker, not Dan. |
| **Decisions only if explicit** | Reduces hallucinated decisions; empty list is acceptable. |
| **Integrity checklist at the end** | Repetition helps compliance before the long transcript. |

---

## 3. Where I got stuck and how I fixed it
*1) Too many (or wrong) participants*=
**Problem:** The model sometimes listed more participants than there was, it couldnt distinguish well btween “someone who spoke” and “someone only mentioned.”

**What I did:** Tightened the summarization prompt and server-side rules (e.g. only people with spoken lines, filter absent or third-party mentions). That improved results a lot.

**Limit:** It is still not perfect because we do not run true speaker diarization—the transcript is mostly one block of text, so “who spoke” is inferred, not measured per utterance.

*2) Transcript is not per person (no “who said what”)*
**Problem:** For a real meeting brief you often want turn-by-turn or at least labeled speakers. Our pipeline uses Whisper-style transcription that returns plain text, so speaker identification stays best-effort (names when the text supports it, otherwise generic labels).

**If I had more time:** Add a diarization step before or after transcription, for example:
- Use a service or model that outputs time-stamped segments per speaker, then merge those segments with the transcript;  
- Use a single stack that returns word- or segment-level speaker labels and feed that text into the summarizer so `participants` and quotes align with real turns.

That would cost more engineering and often more API usage, but it is the right fix when the product must answer “who said what.”

*3) Deployment and protecting API credits*
**Problem:** Once the app is public, anyone with the URL could trigger paid calls (Whisper + LLM) and burn through credits.

**What I implemented:** Google Sign-In on the frontend, token verification on the backend, and MongoDB-backed users with an allowlist and per-user summary quota (plus optional rate limiting). In production you turn this on with settings like `AUTH_ENABLED` so only approved, signed-in users consume summarization.

---

## 4. How long it actually took
Backend (upload, transcribe, summarize, cache) - ~3 h 
Frontend (upload UI, results) - ~2 h 
Extra (authentication, users, deploy) - ~1 h 
**Total (approx.)** - **~6 h** 

---

## 5. Backlog: ideas to make EchoBrief better
This is a **living list** of improvements.

**Docker** (backend image, optional `compose` for API + dependencies later) - Same Python and deps everywhere; easier onboarding, CI, and deploy paths that expect containers. 
**Speaker diarization** - True “who said what” per time segment instead of inferring speakers from one flat transcript; better participants, quotes, and action-item attribution. 
**Transcript UX** - Timestamps, per-speaker lines (once diarization exists), optional audio player with seek-to-segment. 
**Exports** - PDF or other formats alongside DOCX if users ask for them. 
**Observability** - Structured logging and error reporting so production issues are diagnosable without guessing. 
**a11y / polish** - Keyboard flow, focus, labels—makes the app usable for more people and often improves quality for everyone. 
**HttpOnly session cookies** - After Google sign-in, verify the ID token once on the API, then issue a server session in an `HttpOnly; Secure` cookie instead of keeping the token in `sessionStorage` and sending `Authorization: Bearer`. Frontend uses `fetch` with `credentials: 'include'`; Render CORS must allow the Vercel origin with credentials (and `SameSite=None; Secure` on the cookie while the app and API are on different registrable domains). Optional: align `app.` + `api.` under one domain to simplify SameSite. Fine to defer past the demo; worth doing before treating auth as production-hardened.

---

## Appendix: pointers in this repo
- Technical overview (repo state): `plan/PROCESS.md`  
- Numbered phase plans: `plan/01-*.md` through `plan/11-*.md` (order: `plan/the-process-for-me.md`)  

---
