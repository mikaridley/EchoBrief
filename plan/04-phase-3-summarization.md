## Goal
Implement Phase 3: turn a transcript into strict, validated JSON:
- `summary` (string)
- `participants` (list of strings)
- `decisions` (list of strings)
- `action_items` (list of `{task, owner?, due?}`)

## Approach
- Use OpenAI **Responses API** with a constrained prompt and **JSON-only** output.
- Validate output using Pydantic models (schema already exists in `backend/app/schemas/meeting.py`).
- Add a **single retry** if JSON is malformed (“fix JSON” prompt).
- Add **caching** keyed by transcript hash to avoid repeated calls during dev.
- Add `SUMMARIZATION_ENABLED` + a small local rate limit to avoid accidental spend.

## Key prompt choices (why)
- **JSON-only + schema**: reduces UI glue and parsing errors.
- **Anti-hallucination rules**: empty lists over guessing; only include owners/dates when stated.
- **Short summary**: readable and consistent in the UI + docx.

## Questions (answer before final polish)
1. Which model should we use for summarization to balance cost/quality?
   - Default suggestion: `gpt-5.4-mini` (cheap enough, good structured output).
2. Do you want to include a `confidence` or `notes` field in the response?
   - Default: **no** (keep API contract minimal).

