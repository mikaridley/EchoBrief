## Goal
Limit uploaded audio/video to **5 minutes**. If the file is longer, **crop to the first 5 minutes** before sending it to Whisper.

## Why this matters
- Whisper costs scale with audio length. Capping length protects the OpenAI bill and keeps latency predictable.
- We already cap **size** (`MAX_UPLOAD_MB`); duration is the missing piece.

---

## Where to enforce — 3 options

### Option A — Backend crop with `ffmpeg` (most reliable)
- Detect duration with `ffprobe`. If > 5 min, run `ffmpeg -i in -t 300 -c copy out` (stream-copy, near-instant) and send the cropped file to Whisper.
- **Pros**: works for any container (`mp4`, `webm`, `m4a`, `mp3`, `wav`...), exact duration, single source of truth.
- **Cons**: requires `ffmpeg` binary on the server. On Render we'd need a custom build step (apt install or `imageio-ffmpeg` Python wheel that ships a static binary).

### Option B — Backend reject only (no crop)
- Detect duration, return `413` with a friendly message: "Max 5 minutes. Yours is X." User trims locally.
- **Pros**: simplest, no ffmpeg needed.
- **Cons**: contradicts your request ("just crop it"), worse UX.

### Option C — Frontend crop with Web Audio API
- Decode in browser, take first 300s, re-encode (e.g. to wav).
- **Pros**: no backend changes.
- **Cons**: heavy, slow on big files, re-encoding to wav balloons size, hard for video containers.

---

## Recommended: **Option A** + a small frontend pre-check

1. **Frontend** (cheap UX win, not a security boundary):
   - When the user picks a file, read `audio.duration` from the existing `<audio preload="metadata">` element.
   - If `> 300s`, show a non-blocking notice: "Only the first 5 minutes will be processed."
2. **Backend** (the real enforcement):
   - Add `MAX_AUDIO_DURATION_SEC = 300` to `config.py`.
   - Use `imageio-ffmpeg` (ships a static `ffmpeg` binary as a pip wheel — no system install, works on Render) to:
     - probe duration,
     - if longer, stream-copy the first 300s into a new temp file,
     - hash & cache **the cropped bytes** (so the cache key reflects what was actually transcribed),
     - pass that file to `transcribe_audio`.

---

## Questions (please answer before I code)

1. **ffmpeg install path**: OK with adding `imageio-ffmpeg` to `backend/requirements.txt`? It's the cleanest way to get ffmpeg on Render without changing the build environment. Alternative is `apt install ffmpeg` via a Render build command.
2. **Frontend behavior** when duration > 5 min:
   - (a) **Auto-proceed** with a yellow notice "Only first 5 min will be processed", OR
   - (b) **Block upload** with an error and require the user to trim first?
   I recommend (a) since you said "just crop it".
3. **Cache key** after cropping: should the cache hash be on the **cropped** bytes (so re-uploading the same long file hits cache) or the **original** bytes (simpler, but cropped result is what's stored)? I recommend **cropped** — cleaner semantics.
4. **Make the limit configurable** via env var `MAX_AUDIO_DURATION_SEC` (default 300), or hardcode `300` for now? I recommend env var, mirroring `MAX_UPLOAD_MB`.

## Plan after answers
- `backend/requirements.txt`: add `imageio-ffmpeg`.
- `backend/app/core/config.py`: add `max_audio_duration_sec`.
- `backend/app/services/audio_crop.py` (new): `probe_duration()`, `crop_to_seconds()`.
- `backend/app/api/routes/process.py`: after writing the temp file, probe → if too long, crop → recompute hash on cropped bytes → continue as today.
- `frontend/src/cmps/AudioUpload.jsx`: read `audio.duration` on file pick, show notice if > 300s.
