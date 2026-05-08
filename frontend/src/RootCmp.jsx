import { useState } from 'react'

export default function RootCmp() {
  const [count, setCount] = useState(0)

  function onIncrement() {
    setCount((prevCount) => prevCount + 1)
  }

  return (
    <main className="app">
      <section className="app__content">
        <h1 className="app__title">EchoBrief</h1>
        <p className="app__subtitle">
          This is the new React root component, ready to implement your Figma UI.
        </p>

        <button className="btn" type="button" onClick={onIncrement}>
          Count is {count}
        </button>
      </section>
    </main>
  )
}
