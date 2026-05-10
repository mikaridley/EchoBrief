import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { GoogleOAuthProvider } from '@react-oauth/google'

import './assets/styles/main.css'

import RootCmp from './RootCmp'
import { AuthProvider } from './auth/AuthContext'

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

const rootEl = document.getElementById('root')
if (!rootEl) {
  throw new Error('Missing #root element')
}

createRoot(rootEl).render(
  <StrictMode>
    {googleClientId ? (
      <GoogleOAuthProvider clientId={googleClientId}>
        <AuthProvider>
          <RootCmp />
        </AuthProvider>
      </GoogleOAuthProvider>
    ) : (
      <AuthProvider>
        <RootCmp />
      </AuthProvider>
    )}
  </StrictMode>,
)
