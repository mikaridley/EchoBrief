## Goal
Add a friendly audio upload input in the frontend that sends the selected audio file to the backend endpoint `POST /api/process` (FastAPI), using multipart/form-data with the field name `file`.

## Assumptions I’m making (so we can move fast)
- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:5173`
- The backend expects `file` as the multipart field (confirmed in `backend/app/api/routes/process.py`)

## Questions (answer later, code will still work now)
- Do you want the UI to show the returned `transcript`/`summary` on the page, or only show “Uploaded successfully”?
- Do you want upload progress (requires `XMLHttpRequest`) or is “Uploading…” enough for now?

## Plan
- Add `VITE_API_BASE_URL` support with a safe default (`http://localhost:8000`)
- Create `process.service.js` with `uploadAudioForProcessing(file)` that calls `POST {baseUrl}/api/process`
- Build `AudioUpload` component:
  - drag & drop zone + file picker
  - validates type/size lightly on client
  - upload button + loading/error/success states
  - optionally renders response (transcript/summary)
- Style it in `assets/styles/cmps/audio-upload.css` and import it from `assets/styles/cmps/_cmps.css`
- Render it in `Home.jsx`

