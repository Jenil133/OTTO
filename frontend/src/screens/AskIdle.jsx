import { useState } from 'react'
import './askidle.css'
import Orb from '../components/Orb.jsx'
import { MOCK_USER_TEXT } from '../mockRun.js'

const CHIPS = [
  'find new-grad SDE roles at…',
  'watch this price and tell me',
  'compare flights to Tokyo',
]

/**
 * Ask-idle — "Ask, and it's done" landing screen.
 * Props-driven only: renders from { state }, talks back via dispatch/onRun.
 */
export default function AskIdle({ state, dispatch, onRun }) {
  const [text, setText] = useState('')

  const submitTyped = () => {
    const t = text.trim()
    if (!t) return
    onRun(t)
    setText('')
  }

  const handlePressStart = () => {
    dispatch({ type: 'ui/orb', orb: 'recording' })
  }

  const handlePressEnd = () => {
    if (state.orb === 'recording') onRun(MOCK_USER_TEXT)
  }

  return (
    <div className="idle-screen">
      <div className="idle-wordmark">otto</div>

      <div className="idle-center">
        <Orb
          mode={state.orb}
          size={120}
          onPressStart={handlePressStart}
          onPressEnd={handlePressEnd}
        />

        <h1 className="idle-h1">Ask, and it’s done</h1>
        <p className="idle-sub">3 agents standing by · every action logged</p>

        <div className="idle-chips">
          {CHIPS.map((chip) => (
            <button
              key={chip}
              type="button"
              className="idle-chip"
              onClick={() => onRun(MOCK_USER_TEXT)}
            >
              {chip}
            </button>
          ))}
        </div>

        <input
          type="text"
          className="idle-input"
          value={text}
          placeholder="or type it — ask anything"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.nativeEvent.isComposing) submitTyped() }}
        />
      </div>

      <div className="idle-footer mono">
        <span className="idle-stat">
          <span className="dot done" /> memory · {state.memory.preferences.length} preferences
        </span>
        <span className="idle-stat">
          <span className="dot done" /> gateway ok
        </span>
        <span className="idle-stat">
          <span className="dot idle" /> watch idle
        </span>
      </div>
    </div>
  )
}
