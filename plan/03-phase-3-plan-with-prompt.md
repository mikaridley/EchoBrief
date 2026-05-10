## Phase 3 — Summarization (LLM) plan

### Goal
Given a transcript string, produce **strict JSON** with:
- `summary: string`
- `participants: string[]`
- `decisions: string[]`
- `action_items: { task: string, owner: string|null, due: string|null }[]`

Return this in the existing API response (`ProcessResponse`) and keep it reliable + cheap to iterate on.

---

## Prompt (primary)
This is the prompt we will send to the model:

```
### Role
You are an expert Executive Assistant and Meeting Analyst. Your goal is to extract high-value insights from meeting transcripts with 100% accuracy.

### Task
Analyze the provided transcript and generate a structured summary, participant list, key decisions, and action items.

### Output Format
Return ONLY a valid JSON object. Do not include any conversational text, markdown blocks (like ```json), or explanations. 

Schema:
{
  "summary": "A concise 2-3 sentence overview of the meeting's purpose and outcome.",
  "participants": ["Name or Role, or Anonymous Identifier (e.g., 'Speaker 1')"],
  "decisions": ["Clear, specific outcomes or agreements reached"],
  "action_items": [
    {
      "task": "The specific task to be completed",
      "owner": "Name of the person responsible or null",
      "due": "Deadline mentioned or null"
    }
  ]
}

### Strict Rules
1. Language: The JSON values MUST be in the same language as the transcript.
2. Participants: Identify participants from speaker labels or context. If unknown, use [].
3. Decisions: Only include confirmed decisions. Do not include suggestions that were rejected.
4. Action Items: Tasks must be actionable. If an owner is implied (e.g., "I will take care of that, Sarah"), assign it correctly.
5. Integrity: Never fabricate information. If a field has no data, return an empty list or null.

### Transcript
[INSERT TRANSCRIPT HERE]
```

### Why this prompt
- **JSON-only**: avoids post-processing and reduces UI bugs
- **No extra keys**: keeps contract stable
- **Anti-hallucination** rules: protects correctness on messy audio

---

## Retry prompt (“fix JSON once”)
If the output is not valid JSON or fails schema validation, we retry once with:

```
Fix the following output to be ONLY valid JSON matching the schema.
Do not add extra keys.

Bad output:
<MODEL_OUTPUT_HERE>
```

### Why retry once
- Keeps cost bounded
- Fixes common “almost JSON” failures

---

## Validation rules (server-side)
- Parse JSON (`json.loads`)
- Reject if:
  - output is not an object
  - extra keys exist
  - `summary` is empty
  - `action_items` items fail Pydantic (`ActionItem`)

---

## Cost controls (important for dev)
- **Cache summaries** by transcript hash:
  - path: `backend/.cache/summaries/<sha256>.json`
  - same transcript → no new API call
- **Enable switch**: `SUMMARIZATION_ENABLED=0` returns stub fields
- **Local rate limit**: `SUMMARIZATION_MAX_CALLS_PER_MIN`

---

## Integration steps
- Add `backend/app/services/summarize.py` with `summarize_transcript(...)`
- Wire it into `POST /api/process` after Whisper transcription
- Store LLM model version into `meta.model_versions.llm`
- Surface caching in `meta.cached`

---

## Questions (answer before “final prompt lock”)
1. **Summarization model**: do you want `gpt-5.4-mini` (cheap) or a higher-quality model for better extraction?
yes i want the cheapest
2. **Participants**: should we try to infer speaker names (“Speaker 1/2”) if names aren’t present, or keep `[]`?
yes speaker 1 and 2 sounds good, if you can identify if its female/male add that.
3. **Summary style**: 1 paragraph max, or allow 3–5 bullet points?
bullet boints is the best

