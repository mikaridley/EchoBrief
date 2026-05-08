import logoUrl from '../assets/imgs/logo-minimal.svg'

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="app-header__inner">
        <a className="app-header__logo" href="/" aria-label="EchoBrief home">
          <img className="app-header__logo-img" src={logoUrl} alt="" />
          <span className="app-header__logo-text">EchoBrief</span>
        </a>

        <nav className="app-header__nav" aria-label="Primary">
          <a className="app-header__link" href="/">
            Home
          </a>
          <a className="app-header__link" href="/about-team">
            About the team
          </a>
        </nav>
      </div>
    </header>
  )
}

