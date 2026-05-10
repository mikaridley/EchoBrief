import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Do not set Cross-Origin-Opener-Policy on the Vite dev server: `server.headers` applies to every
// response (including @vite/client), and COOP breaks that client’s window.postMessage (HMR, etc.).
// Production uses `vercel.json` so Google sign-in still gets same-origin-allow-popups on deploy.
export default defineConfig({
  plugins: [react()],
})
