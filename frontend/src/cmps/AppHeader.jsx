import logoUrl from '../assets/imgs/logo-minimal.svg'
import { NavLink } from 'react-router-dom'

export function AppHeader() {
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
        </nav>
      </div>
    </header>
  )
}

