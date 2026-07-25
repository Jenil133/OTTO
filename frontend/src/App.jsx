import { useEffect, useReducer, useRef } from 'react'
import { initialState, reducer } from './store.js'
import { playMockRun, MOCK_USER_TEXT } from './mockRun.js'
import { connectEvents, postTask } from './ws.js'
import NavRail from './components/NavRail.jsx'
import AskIdle from './screens/AskIdle.jsx'
import AskLive from './screens/AskLive.jsx'
import Results from './screens/Results.jsx'
import Memory from './screens/Memory.jsx'
import Watches from './screens/Watches.jsx'
import Connect from './screens/Connect.jsx'

const params = new URLSearchParams(window.location.search)
const SPEED = Number(params.get('speed')) || 1
// ?mock=1 is the Phase 1 default; the real WS client slots in behind the
// same dispatch({type:'event'}) interface in Phase 2.
const MOCK = params.get('mock') !== '0'

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState)
  const cancelRef = useRef(null)

  const startRun = (text) => {
    cancelRef.current?.()
    dispatch({ type: 'ui/start_run', text })
    if (MOCK) cancelRef.current = playMockRun(dispatch, { speed: SPEED })
    else postTask(text) // fire and forget — run.id arrives via the plan event
  }

  // Golden replay is ALWAYS the canned mock run, even with ?mock=0 — it's the
  // demo-night safety net (D7): if the live backend stalls, `g` still plays a
  // full believable run instead of posting to a dead server.
  const playGolden = () => {
    cancelRef.current?.()
    dispatch({ type: 'ui/start_run', text: MOCK_USER_TEXT })
    cancelRef.current = playMockRun(dispatch, { speed: SPEED })
  }

  // real WS /events → same dispatch({type:'event'}) pipe as the mock engine
  useEffect(() => {
    if (MOCK) return
    return connectEvents(dispatch)
  }, [])

  // auto-advance to results for BOTH paths once Otto is speaking.
  // (mockRun's own ui/run_complete timer stays; the action is idempotent.)
  useEffect(() => {
    if (state.run?.status !== 'speaking') return
    const t = setTimeout(() => dispatch({ type: 'ui/run_complete' }), 2500)
    return () => clearTimeout(t)
  }, [state.run?.status])

  // hotkeys: g = golden-run replay (demo-night safety net, D7)
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
      if (e.key === 'g') playGolden()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => () => cancelRef.current?.(), [])

  const screens = {
    ask: <AskIdle state={state} dispatch={dispatch} onRun={startRun} />,
    live: <AskLive state={state} dispatch={dispatch} onRun={startRun} />,
    results: <Results state={state} dispatch={dispatch} onRun={startRun} />,
    memory: <Memory state={state} dispatch={dispatch} />,
    watches: <Watches state={state} dispatch={dispatch} />,
    connect: <Connect state={state} dispatch={dispatch} />,
  }

  return (
    <div className="shell">
      <NavRail
        screen={state.screen}
        onNavigate={(screen) => dispatch({ type: 'ui/navigate', screen })}
      />
      <main className="main">
        <div className="screen" key={state.screen}>
          {screens[state.screen] ?? screens.ask}
        </div>
      </main>
    </div>
  )
}
