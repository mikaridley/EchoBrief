import logoUrl from '../assets/imgs/logo-minimal.svg'
import { NavLink } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import { useRef } from 'react'
import { useAuth } from '../context/AuthContext.jsx'

export function AppHeader() {
  const { me, isLoading, onLoginSuccess, logout } = useAuth()
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
  const googleLoginMountRef = useRef(null)

  function onLoginClick() {
    const el = googleLoginMountRef.current
    if (!el) return

    const btn = el.querySelector('div[role="button"]')
    if (!btn) return

    btn.click()
  }

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <NavLink className="app-header__logo" to="/" aria-label="EchoBrief home">
          <img className="app-header__logo-img" src={logoUrl} alt="" />
          <span className="app-header__logo-text">EchoBrief</span>
        </NavLink>

        <nav className="app-header__nav" aria-label="Primary">
          <NavLink
            className={({ isActive }) =>
              isActive ? 'app-header__link is-active' : 'app-header__link'
            }
            to="/"
            end
          >
            Home
          </NavLink>
          <NavLink
            className={({ isActive }) =>
              isActive ? 'app-header__link is-active' : 'app-header__link'
            }
            to="/about-team"
          >
            About the team
          </NavLink>

          <div className="app-header__auth" aria-label="Authentication">
          {isLoading && <span className="app-header__auth-status">…</span>}

          {!isLoading && !me && (
            <>
              {!googleClientId && <span className="app-header__auth-status">Set VITE_GOOGLE_CLIENT_ID</span>}
              {!!googleClientId && (
                <>
                  <button className="app-header__auth-btn" type="button" onClick={onLoginClick}>
                    Log in
                  </button>
                  <span className="app-header__google-login-mount" ref={googleLoginMountRef} aria-hidden="true">
                    <GoogleLogin
                      onSuccess={(res) => onLoginSuccess(res?.credential || '')}
                      onError={() => {}}
                      useOneTap={false}
                    />
                  </span>
                </>
              )}
            </>
          )}

          {!isLoading && me && (
            <button className="app-header__auth-btn" type="button" onClick={logout} title={me.email}>
              Sign out
            </button>
          )}
        </div>
        </nav>


      </div>
    </header>
  )
}

