# 001 - Header component (logo + navbar)

## Goal
Add an `AppHeader` with:
- Logo on the top-left
- Navbar links: Home, About the team

## Assumptions (so we can move fast)
- No router is set up yet, so links will be plain links (`/`, `/about-team`) as placeholders until we add routing.
- We’ll use the existing `frontend/src/assets/imgs/logo-minimal.svg` as the logo image.

## Questions (answer when you can)
- Do you want the **brand name text** next to the logo (e.g. “EchoBrief”), or logo-only?
- Should **About the team** be a real page later (React Router)?

## Steps
- Create `frontend/src/cmps/AppHeader.jsx`
- Add `frontend/src/assets/styles/cmps/app-header.css`
- Import that CSS from `frontend/src/assets/styles/cmps/_cmps.css`
- Render `AppHeader` in `frontend/src/RootCmp.jsx`
- Keep the home page as the current page; add the “About the team” page later

