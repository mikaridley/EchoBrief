## Goal
Make the `backend/` codebase clear, minimal, and “industry professional”: predictable structure, clean config/env handling, safe logging, consistent error handling, and no stray dev/test artifacts in runtime paths.

## What I’ll review
- Entry point (`app/main.py`) and app factory/lifespan setup
- Routing layout (`app/api/routes/*`), including any “test” routes
- Core layer (`app/core/*`): config, auth, db wiring
- Services (`app/services/*`): boundaries, side-effects, naming
- Schemas/models (`app/schemas/*`)
- Dependency & runtime setup (`requirements.txt`, `.env.example`)
- Scripts and one-off files under `backend/` root

## What I’ll deliver
- A punch-list of **unnecessary / risky / unprofessional** items
- Recommended structure and conventions (what to keep, what to move, what to delete)
- If safe, small refactors to improve clarity (no behavior changes unless needed)

