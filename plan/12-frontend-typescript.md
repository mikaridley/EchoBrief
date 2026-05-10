# 12 — Frontend TypeScript migration

## Goal
Move `frontend/` from JS/JSX to TS/TSX with strict checking aligned to the backend `ProcessResponse` / `/auth/me` shapes.

## Steps (done in this pass)
1. Add `typescript`, `tsconfig.json` + `tsconfig.node.json`, `src/vite-env.d.ts`.
2. Add shared API types under `src/types/api.ts`.
3. Rename and type all `src/**` modules; point `index.html` at `index.tsx`.
4. Convert `vite.config.js` → `vite.config.ts`; extend ESLint for TS.
5. Run `npm install`, `npm run build` (includes `tsc --noEmit`).

## Questions
_None — user approved full migration._
