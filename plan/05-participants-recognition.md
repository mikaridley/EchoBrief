## Goal
Make `participants` reflect **the real number of speakers** in the meeting,
using real names when context allows, generic placeholders otherwise,
and never returning an empty list when the transcript is non-empty.

---

## Current behavior (the bug)
Whisper-1 returns plain text (no `Speaker 1:` labels).

The current prompt forbids inferring names from context (`Speaker Identification (NO GUESSING)`),
and the safety net `_enforce_speaker_only_participants` filters out anything
that isn't matched by the regex `^Speaker \d+:` in the transcript.

Combined effect on an undiarized Whisper transcript:
- LLM returns `["Speaker 1"]` (forced by the prompt).
- Safety net wipes it because no `Speaker 1:` label exists in the transcript.
- Result: `participants = []`. ← bug.

---

## What we want
1. LLM **estimates speaker count** from conversational cues.
2. If LLM can confidently identify a speaker's name from context → use the real name.
3. Otherwise → `Speaker 1`, `Speaker 2`, etc.
4. If transcript is non-empty, `participants` is **never** empty (fallback: `["Speaker 1"]`).
5. Hallucination guard: `action_items[].owner` must be in `participants` or `null`.

---

## Plan

### 1. Update the prompt (`_make_prompt`)
Replace the strict "no guessing" section with:
- "Identify how many distinct people **actively speak** in the transcript."
- "If a speaker introduces themselves, is addressed by name, or context strongly implies their identity, use that name. Otherwise use `Speaker 1`, `Speaker 2`, ... in the order they first speak."
- "Do **not** include people who are only mentioned (third parties), groups, teams, or companies."
- "If the transcript has any content, `participants` MUST contain at least one item."
- Keep the action-item ownership constraint (owner ∈ participants or `null`).

### 2. Replace the safety net
Rename `_enforce_speaker_only_participants` → `_enforce_participants_non_empty`.

New logic:
- Trust the LLM's `participants` list as-is (strings, non-empty, deduped).
- If the list is empty AND transcript is non-empty → fallback to `["Speaker 1"]`.
- For each `action_item.owner`: if not in `participants` → set to `null`.

We **drop** the regex-based "must match `^Speaker N:` in transcript" filter,
because Whisper-1 never produces those labels. The prompt + ownership check are enough.

### 3. Bump `_DEFAULT_PROMPT_VERSION`
`'2026-05-07-1'` → `'2026-05-08-1'` so old caches are invalidated cleanly.

### 4. Manual smoke test
- Re-run the tour video transcript → expect `participants` to be non-empty
  (likely `["Speaker 1"]`, since the narrator is the only active speaker; brother Tom and Rich/Glenn are mentioned).
- Re-run the team-sync transcript → expect `["Speaker 1", "Speaker 2"]` (no real names available),
  not `["Rotem", "Marketing team"]`.

---

## Trade-offs (why this approach)
- **Versus dropping the safety net entirely**: we keep the action-item ownership check, which is the real anti-hallucination value.
- **Versus keeping the regex filter**: pointless with Whisper-1 — it never produces `Speaker N:` labels.
- **Versus adding diarization (pyannote / external service)**: out of scope, expensive, big change. We'd revisit later if quality demands it.

---

## Questions (answer before I implement)
1. **Confidence threshold for real names**: should the prompt say "use a real name **only when explicitly self-introduced or directly addressed**" (strict), or allow "**strongly implied by context**" (looser, more risk of wrong attribution)?
   → **both**: self-introduced or strongly implied by context.
2. **Gender hint** (carried over from plan 003 Q2): do you still want the LLM to add `(female)` / `(male)` to placeholders like `Speaker 1 (female)` when audible? Or drop that idea now that Whisper-1 gives us no audio cues anyway?
   → **drop it**.
