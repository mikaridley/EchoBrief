import { useEffect, useMemo, useRef, useState } from 'react'

const WORDS = [
  'transcripts',
  'notes',
  'summaries',
  'action items',
  'insights',
  'follow-ups',
]

export function Hero() {
  const [idx, setIdx] = useState(0)
  const [visibleCount, setVisibleCount] = useState(0)
  const timeoutsRef = useRef([])
  const [isReducedMotion, setIsReducedMotion] = useState(false)

  const currentWord = WORDS[idx]
  const chars = useMemo(() => currentWord.split(''), [currentWord])
  const maxLen = useMemo(() => WORDS.reduce((acc, w) => Math.max(acc, w.length), 0), [])
  const typedText = useMemo(
    () => currentWord.slice(0, Math.min(visibleCount, currentWord.length)),
    [currentWord, visibleCount]
  )

  useEffect(() => {
    const mediaQuery = window.matchMedia?.('(prefers-reduced-motion: reduce)')
    if (!mediaQuery) return

    const update = () => setIsReducedMotion(Boolean(mediaQuery.matches))
    update()

    if (mediaQuery.addEventListener) mediaQuery.addEventListener('change', update)
    else mediaQuery.addListener(update)

    return () => {
      if (mediaQuery.removeEventListener) mediaQuery.removeEventListener('change', update)
      else mediaQuery.removeListener(update)
    }
  }, [])

  useEffect(() => {
    if (isReducedMotion) return
    const TYPE_MS = 100
    const DELETE_MS = 90
    const HOLD_FULL_MS = 3000
    const HOLD_EMPTY_MS = 500

    const clearAll = () => {
      timeoutsRef.current.forEach((t) => window.clearTimeout(t))
      timeoutsRef.current = []
    }

    const schedule = (fn, ms) => {
      const t = window.setTimeout(fn, ms)
      timeoutsRef.current.push(t)
      return t
    }

    clearAll()
    let count = 0

    const typeStep = () => {
      count = Math.min(count + 1, chars.length)
      setVisibleCount(count)

      if (count < chars.length) schedule(typeStep, TYPE_MS)
      else schedule(deleteStep, HOLD_FULL_MS)
    }

    const deleteStep = () => {
      count = Math.max(count - 1, 0)
      setVisibleCount(count)

      if (count > 0) schedule(deleteStep, DELETE_MS)
      else {
        schedule(() => {
          setIdx((prevIdx) => (prevIdx + 1) % WORDS.length)
        }, HOLD_EMPTY_MS)
      }
    }

    schedule(typeStep, 260)

    return clearAll
  }, [isReducedMotion, idx, chars.length])

  return (
    <section className="hero" aria-label="Hero">
      <h1 className="hero__title">
        <span className="hero__title-static">Turn meetings into </span>

        <span
          className="hero__rotator"
          aria-live="polite"
          aria-atomic="true"
        >
          <span className="hero__word" style={{ '--word-ch': maxLen }}>
            <span className="hero__typed" aria-hidden="true">
              {typedText || '\u00A0'}
            </span>

            <span className="hero__caret" aria-hidden="true" />

            <span className="hero__sr">{currentWord}</span>
          </span>
        </span>
      </h1>
    </section>
  )
}

