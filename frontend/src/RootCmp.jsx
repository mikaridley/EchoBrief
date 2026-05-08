import { AppHeader } from './cmps/AppHeader.jsx'
import { Home } from './pages/Home.jsx'

export default function RootCmp() {
  return (
    <main className="app-layout">
      <AppHeader />

      <section className="app__content">
        <Home />
      </section>
    </main>
  )
}
