## EchoBrief frontend (React + Vite)

### Setup (Google login)
You must create a **Google OAuth Web Client** and add `http://localhost:5173` to **Authorized JavaScript origins**.

Then create `frontend/.env` (copy from `frontend/.env.example`) and set:
- `VITE_GOOGLE_CLIENT_ID`
- `VITE_API_BASE_URL` (your backend URL, e.g. `http://localhost:8001`)

If Google shows `400 invalid_request`, it’s almost always one of:
- Wrong client type (must be **Web**)
- Missing origin `http://localhost:5173`
- Missing/empty `VITE_GOOGLE_CLIENT_ID`
- OAuth consent screen in **Testing** and your email not in **Test users**

### Run
```bash
npm install
npm run dev
```

---
Below is the original Vite template README (kept for reference).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
