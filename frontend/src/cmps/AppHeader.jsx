import logoUrl from '../assets/imgs/logo-minimal.svg'
import { NavLink } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import { useEffect, useId, useState } from 'react'
import { Menu, X } from 'lucide-react'
import { useAuth } from '../context/useAuth.js'

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
    function onKeyDown(ev) {
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

        <nav
          id={menuId}
          className={`app-header__nav ${isMenuOpen ? 'is-open' : ''}`}
          aria-label="Primary"
        >
          <NavLink
            className={({ isActive }) =>
              isActive ? 'app-header__link is-active' : 'app-header__link'
            }
            to="/"
            end
            onClick={closeMenu}
          >
            Home
          </NavLink>
          <NavLink
            className={({ isActive }) =>
              isActive ? 'app-header__link is-active' : 'app-header__link'
            }
            to="/about-team"
            onClick={closeMenu}
          >
            About
          </NavLink>

          <div className="app-header__auth-stack">
            <div className="app-header__auth" aria-label="Authentication">
              {isLoading && !me && <span className="app-header__auth-status">…</span>}

              {!me && (
                <>
                  {!googleClientId && (
                    <span className="app-header__auth-status">Set VITE_GOOGLE_CLIENT_ID</span>
                  )}
                  {!!googleClientId && (
                    <div className="app-header__google-signin" title="Sign in with Google">
                      <GoogleLogin
                        click_listener={() => clearAuthError()}
                        containerProps={{ className: 'app-header__gsi-button-root' }}
                        onSuccess={(res) => onLoginSuccess(res?.credential || '')}
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

