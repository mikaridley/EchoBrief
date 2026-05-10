import mikaImg from '../assets/imgs/mika-img.jpeg'

export function AboutTeam() {
  return (
    <section className="about-team">
      <h1 className="app__title">Hi, nice to meet ya!</h1>
      <h2 className="app__subtitle">I'm Mika Ridley</h2>

      <img className="about-team__img" src={mikaImg} alt="Mika" />

      <p>I am a Full Stack Developer who loves building with code and AI. I like to think three steps ahead to ensure the technology aligns with business goals, while always striving to learn something new. I’m a fast learner who stays curious, works hard, and keeps things simple. I’m also big on clear communication and just want to build great stuff with good people.</p>

      <h2>Let's Work Together!</h2>
    </section>
  )
}
