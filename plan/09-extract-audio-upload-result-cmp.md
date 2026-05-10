## Goal
Extract the “results” UI from `frontend/src/cmps/AudioUpload.jsx` into its own component, so `AudioUpload` only orchestrates state and actions.

## Why this approach
- **Chosen**: Move the JSX into a new `AudioUploadResult` component and pass data/actions via props.
- **Over alternative (context/store refactor)**: Keeping state in `AudioUpload` avoids widening scope (no new store/service changes) and keeps the refactor safe.

## Questions (answer later)
- Should `AudioUploadResult` eventually format the response into “Transcript / Summary” sections instead of showing raw JSON?
- Do we want the result view to include a “copy to clipboard” action?

## Done
- Created `frontend/src/cmps/AudioUploadResult.jsx`
- Replaced inline result JSX in `AudioUpload.jsx` with `<AudioUploadResult />`

