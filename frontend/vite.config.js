import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// COOP: Google Identity Services / Sign-In may use a popup; without this, some browsers show a blank window.
// https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid#cross_origin_opener_policy
export default defineConfig({
  plugins: [react()],
  server: {
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin-allow-popups',
    },
  },
})
