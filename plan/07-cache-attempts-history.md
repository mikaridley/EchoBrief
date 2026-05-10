## Goal
Turn the summary cache into a **history log** per transcript:
one JSON file per transcript with a list of **attempts** for different
`(model, prompt_version)` combinations. Never delete old attempts.

## File format
`backend/.cache/summaries/<transcript_hash>.json`

```json
{
  "transcript_hash": "f00158cc...",
  "attempts": [
    {
      "model": "gpt-5.4-mini",
      "prompt_version": "2026-05-07-1",
      "created_at": "2026-05-08T14:15:00Z",
      "summary": "...",
      "participants": [...],
      "decisions": [...],
      "action_items": [...]
    },
    { ... another attempt ... }
  ]
}
```

`transcript_hash` = `sha256(normalized_transcript)` only (no model, no version).

## Lookup behavior
1. Compute `transcript_hash`.
2. Read `<transcript_hash>.json`.
3. Find attempts where `attempt.model == model AND attempt.prompt_version == prompt_version`.
4. If any → return the **latest** of those (last in list). `cached: true`. No API call.
5. If none → call LLM, append a new attempt, save, return. `cached: false`.

## Decisions (answered)
- Returned result on cache hit → **latest** matching attempt.
- `created_at` timestamp → **add it** (UTC ISO 8601).
- Old cache files (incompatible old format) → **delete**.

## Out of scope (next plan)
- Action item `owner` policy when owner is a third party (current behavior: `null`). Will revisit after cache refactor lands.

## Steps
1. Add helpers:
   - `_cache_key_for_transcript(transcript)` → sha256 of normalized transcript.
   - `_read_attempts_file(path)` → `dict | None` (returns the wrapper dict).
   - `_find_matching_attempt(attempts, model, prompt_version)` → latest match or `None`.
   - `_append_attempt(path, transcript_hash, attempt)` → safe atomic write.
2. Replace cache read/write inside `summarize_transcript`:
   - Read file → look for matching attempt → return it OR call LLM → append → return.
3. Delete obsolete files in `backend/.cache/summaries/` (old single-attempt format).
4. Lint check + smoke test.
