# Plan — Google Auth + Allowlist + Rate Limits (protect API credits)

## Goal (what we’re solving)
Prevent anyone with the frontend link from consuming **our** paid API calls (OpenAI/Whisper/etc.). Only approved users (e.g. interviewers) can trigger server-side summarization.

Non-goal (for now): “public BYOK” (bring your own OpenAI key) for non-approved users.

---

## Recommended solution (high level)
- **Google Sign-In** on the frontend
- Backend verifies Google ID token (or session) and creates/updates a `users` record in Mongo
- Backend checks **allowlist/permissions** (Mongo) on every protected endpoint
- Add **rate limiting** (per user + per IP) to prevent accidental spam and abuse
- Admin (you) can **enable/disable** users in Mongo to grant/revoke access instantly

---

## Data model (Mongo)
Create a `users` collection.

Suggested fields:
- `email` (unique, lowercase)
- `name`
- `picture`
- `provider`: `'google'`
- `role`: `'admin' | 'interviewer' | 'user'`
- `enabled`: boolean
- `createdAt`, `lastLoginAt`
- `limits`:
  - `requestsPerMinute`
  - `summariesTotalLimit` (e.g. `5`)
  - `summariesTotalUsed` (starts at `0`)

Optional:
- `notes` (free text)
- `revokedAt`

---

## Auth flow
### Frontend
- Add “Continue with Google”
- After login, obtain a Google **ID token**
- Send ID token to backend (e.g. `Authorization: Bearer <id_token>`)

### Backend
- Verify ID token with Google (audience/client_id check is critical)
- Extract `email`, `name`, `picture`
- Upsert user in Mongo:
  - If new user → create with `enabled=false` by default (unless email is pre-approved)
  - Update `lastLoginAt`
- For protected endpoints:
  - Require verified identity
  - Require `enabled=true`

---

## Access control behavior
### If user is enabled
- Allow API endpoints (summarize/process/docx) to run normally

### If user is NOT enabled
- Backend returns `403 Forbidden` with a clear error code (e.g. `ACCESS_REQUIRED`)
- Frontend shows an “Access required” screen:
  - “You’re signed in as: <email>”
  - “Contact admin: <your email>”

Why this over BYOK right now:
- Keeps your app simple for interviews
- Avoids users pasting API keys into apps (trust/support burden)
- Your backend still needs protection anyway (DB/CPU), so auth is still needed

---

## Rate limiting / quota plan
Add limits even for enabled users.

Targets:
- **Lifetime quota (stored in Mongo)**: **5 summaries total per user** (durable; does not reset on deploy/restart)
- **Anti-spam (optional)**:
  - **Per-user**: e.g. 2 requests/min (in-memory OK for single instance; Redis if multi-instance)
  - **Per-IP** fallback: e.g. 10/min (helps against token theft / scripts)
- **Per-IP** fallback: e.g. 10/min (helps against token theft / scripts)

Implementation options (choose based on current stack):
- **Lifetime quota**: Mongo counter on the user doc (`summariesTotalUsed`)
- **Anti-spam limiter**:
  - **Fast to ship**: in-memory limiter (OK for single-instance deployments; resets on restart)
  - **More correct**: Redis-based limiter (works across multiple instances)
- **Edge** (optional): Cloudflare rate limiting/WAF in front of API

Trade-off:
- Mongo quota is durable and works for any deployment topology
- In-memory anti-spam is simplest but weaker for scaling
- Redis anti-spam is extra infra but robust

---

## Endpoint inventory (what becomes protected)
Protect anything that triggers cost / heavy compute, likely:
- `POST /api/process`
- `POST /api/docx` (optional but recommended)
- Any “history”, “download”, “list results” endpoints (if added later)

Keep public:
- `GET /api/health`

---

## Admin workflow (how you grant/revoke)
MVP admin workflow (fast):
- You manually edit Mongo documents:
  - set `enabled=true` for interviewer emails
  - set `enabled=false` after interview

Optional later:
- Admin-only endpoint / small admin UI:
  - list users
  - toggle enabled
  - view usage counters

---

## Logging & monitoring (minimal but important)
Log (server-side):
- `userId/email`
- endpoint called
- tokens/time spent (if available)
- rejection reasons (rate limit hit, not enabled)

This helps you answer: “who burned credits?”

---

## Implementation steps (sequence)
- Add Google OAuth client (Google Cloud Console)
- Frontend: add Google login + store token in memory (avoid long-lived storage if possible)
- Backend: add token verification middleware/dependency
- Mongo: `users` collection + upsert on login
- Protect endpoints with `enabled` check
- Add rate limiting
- Add “Access required” UI state
- Smoke test:
  - enabled user can summarize
  - disabled user gets 403 and UI message
  - rate limit triggers properly

---

## Open questions (answer these before we implement)
1) Confirmed: new logins default to `enabled=false`.
2) Confirmed: blocked users see “Contact admin”.
3) Confirmed: `summariesTotalLimit = 5` (total, not per-day).
4) Are you deploying as **single instance** (in-memory anti-spam is fine), or might you scale to multiple instances (prefer Redis for anti-spam)? answer: single instance

