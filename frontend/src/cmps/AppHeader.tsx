import logoUrl from '../assets/imgs/logo-minimal.svg'
import { NavLink } from 'react-router-dom'
import { GoogleLogin, type CredentialResponse } from '@react-oauth/google'
import { useEffect, useId, useState } from 'react'
import { Loader2, Menu, X } from 'lucide-react'
import { useAuth } from '../auth/auth.context'

export function AppHeader() {
  const { me, isLoading, authError, clearAuthError, reportGoogleLoginError, onLoginSuccess, logout } = useAuth()
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
  const menuId = useId()

  const [isMenuOpen, setIsMenuOpen] = useState(false)

  function closeMenu() {
    setIsMenuOpen(false)
  }

  function onToggleMenu() {
    setIsMenuOpen((prev) => !prev)
  }

  useEffect(() => {
    function onKeyDown(ev: KeyboardEvent) {
      if (ev.key === 'Escape') closeMenu()
    }

    function onResize() {
      if (window.innerWidth > 650) closeMenu()
    }

    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('resize', onResize)

    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('resize', onResize)
    }
  }, [])

  function onGoogleSuccess(res: CredentialResponse) {
    onLoginSuccess(res.credential || '')
  }

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <NavLink className="app-header__logo" to="/" aria-label="EchoBrief home">
          <img className="app-header__logo-img" src={logoUrl} alt="" />
          <span className="app-header__logo-text">EchoBrief</span>
        </NavLink>

        <button
          className="app-header__burger"
          type="button"
          onClick={onToggleMenu}
          aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={isMenuOpen}
          aria-controls={menuId}
        >
          {isMenuOpen ? <X /> : <Menu />}
        </button>

        <div
          className={`app-header__overlay ${isMenuOpen ? 'is-open' : ''}`}
          onClick={closeMenu}
          aria-hidden={!isMenuOpen}
        />

        <nav id={menuId} className={`app-header__nav ${isMenuOpen ? 'is-open' : ''}`} aria-label="Primary">
          <NavLink
            className={({ isActive }) => (isActive ? 'app-header__link is-active' : 'app-header__link')}
            to="/"
            end
            onClick={closeMenu}
          >
            Home
          </NavLink>
          <NavLink
            className={({ isActive }) => (isActive ? 'app-header__link is-active' : 'app-header__link')}
            to="/about-team"
            onClick={closeMenu}
          >
            About
          </NavLink>

          <div className="app-header__auth-stack">
            <div className="app-header__auth" aria-label="Authentication">
              {!me && (
                <>
                  {!googleClientId && (
                    <span className="app-header__auth-status">Set VITE_GOOGLE_CLIENT_ID</span>
                  )}
                  {!!googleClientId && isLoading && (
                    <div
                      className="app-header__auth-loader"
                      role="status"
                      aria-live="polite"
                      aria-label="Checking sign-in status"
                    >
                      <Loader2 aria-hidden />
                    </div>
                  )}
                  {!!googleClientId && !isLoading && (
                    <div className="app-header__google-signin" title="Sign in with Google">
                      <GoogleLogin
                        click_listener={() => clearAuthError()}
                        containerProps={{ className: 'app-header__gsi-button-root' }}
                        onSuccess={onGoogleSuccess}
                        onError={() => reportGoogleLoginError()}
                        useOneTap={false}
                        type="icon"
                        theme="filled_black"
                        size="medium"
                      />
                    </div>
                  )}
                </>
              )}

              {!isLoading && me && (
                <button className="app-header__auth-btn" type="button" onClick={logout} title={me.email}>
                  Sign out
                </button>
              )}
            </div>
            {authError && !me && (
              <p className="app-header__auth-error" role="alert">
                {authError}
              </p>
            )}
          </div>
        </nav>
      </div>
    </header>
  )
}
