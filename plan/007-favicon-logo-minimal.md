## Goal
Use `logo-minimal` from the `imgs` folder as the browser tab icon (favicon).

## What I’ll change
- Update `frontend/index.html` to reference the SVG at `/src/assets/imgs/logo-minimal.svg`.

## Why this approach
- In Vite, referencing assets from `index.html` via `/src/...` is reliable in dev and gets rewritten for production builds automatically.
- Alternative is copying into `frontend/public/` (works too), but that duplicates files and is unnecessary here.

## Done when
- Reloading the app shows the `logo-minimal` icon in the browser tab.
