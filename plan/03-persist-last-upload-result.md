# Persist last upload result

## Goal
Keep the meeting summary UI after leaving Home or refreshing; clear only on Sign out or "Upload new".

## Approach
- `localStorage` JSON per signed-in user email (key prefix `echobrief:lastProcessResult:`).
- **Why localStorage over sessionStorage:** user asked for survive refreshes; sessionStorage clears when the tab closes.
- **Alternative:** React context lifted to app root — would survive route changes but not refresh unless still backed by storage.

## Steps
1. Add `last-process-result.storage.ts` with load/save/clear + minimal shape validation.
2. `AudioUpload`: hydrate when `me.email` is known; save when `result` becomes non-null; clear storage in `onClearFile` (covers "Upload new").
3. `AuthProvider.logout`: clear stored result for current user before reload.
