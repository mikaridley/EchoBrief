import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { GoogleOAuthProvider } from '@react-oauth/google'

import './assets/styles/main.css'

import RootCmp from './RootCmp.jsx'
import { AuthProvider } from './auth/AuthContext.jsx'

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

createRoot(document.getElementById('root')).render(
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
  </StrictMode>
)
