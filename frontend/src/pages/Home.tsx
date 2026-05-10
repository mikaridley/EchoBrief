import { Hero } from '../cmps/Hero'
import { AudioUpload } from '../cmps/AudioUpload'

export function Home() {
  return (
    <section className="home-page">
      <Hero />

      <section className="home-page__description">
        <h2>
          Stop worrying about missing a meeting. <br />
          Upload your meeting recording and let our AI extract the bottom line for you!
        </h2>
      </section>

      <AudioUpload />
    </section>
  )
}
