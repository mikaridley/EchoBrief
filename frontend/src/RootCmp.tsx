import { AppHeader } from './cmps/AppHeader'
import { Home } from './pages/Home'
import { AboutTeam } from './pages/AboutTeam'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

export default function RootCmp() {
  return (
    <BrowserRouter>
      <main className="app-layout">
        <AppHeader />

        <section className="app__content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about-team" element={<AboutTeam />} />
          </Routes>
        </section>
      </main>
    </BrowserRouter>
  )
}
