import './watches.css'

/**
 * Watches — "Otto checks so you don't."
 * Static screen (Phase 1). Renders ONLY from state.watches.
 * Statuses: 'watching' (amber, pulsing) | 'triggered' (teal) | 'paused' (idle).
 */

const MicIcon = (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="9" y="2.5" width="6" height="11" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0" />
    <line x1="12" y1="18" x2="12" y2="21.5" />
  </svg>
)

const PhoneIcon = (
  <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z" />
  </svg>
)

const PlayIcon = (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polygon points="7 5 18 12 7 19 7 5" />
  </svg>
)

const InfoIcon = (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <line x1="12" y1="11" x2="12" y2="16" />
    <line x1="12" y1="8" x2="12.01" y2="8" />
  </svg>
)

function WatchingCard({ w }) {
  return (
    <div className="card watch-card">
      <div className="watch-row">
        <span className="dot working pulse" />
        <span className="watch-name">{w.title}</span>
        <span className="watch-state watch-state-working">watching</span>
      </div>
      <div className="mono watch-meta">
        {w.target} · {w.cadence} · last check {w.last_check} · now {w.now}
      </div>
      <div className="watch-foot">
        <span className="watch-hist" aria-hidden="true">
          {(w.history ?? []).map((v, i) => (
            <i key={i} className={v ? 'hit' : ''} />
          ))}
        </span>
        <span className="watch-note">
          {PhoneIcon}
          <span>{w.note}</span>
        </span>
      </div>
    </div>
  )
}

function TriggeredCard({ w, dispatch }) {
  return (
    <div className="card watch-card">
      <div className="watch-row">
        <span className="dot done" />
        <span className="watch-name">{w.title}</span>
        <span className="watch-state watch-state-done">triggered {w.triggered_at}</span>
      </div>
      <div className="mono watch-meta">
        {w.target} · {w.cadence}
      </div>
      <div className="watch-foot">
        <span className="watch-alert">
          {PhoneIcon}
          <span>{w.note}</span>
        </span>
        <button
          className="watch-viewrun"
          onClick={() => dispatch({ type: 'ui/navigate', screen: 'results' })}
        >
          view run →
        </button>
      </div>
    </div>
  )
}

function PausedCard({ w }) {
  return (
    <div className="card watch-card watch-card-paused">
      <div className="watch-row">
        <span className="dot idle" />
        <span className="watch-name watch-name-muted">{w.title}</span>
        <button className="btn ghost watch-resume">
          {PlayIcon}
          resume
        </button>
      </div>
    </div>
  )
}

export default function Watches({ state, dispatch }) {
  const watches = state.watches ?? []

  return (
    <div className="watch-page">
      <header className="watch-head">
        <div className="watch-head-left">
          <h1 className="watch-title">Watches</h1>
          <span className="watch-sub">· Otto checks so you don&rsquo;t</span>
        </div>
        <button className="btn primary watch-voice-btn">
          {MicIcon}
          new watch by voice
        </button>
      </header>

      <div className="watch-list">
        {watches.map((w, i) => {
          if (w.status === 'watching') return <WatchingCard key={i} w={w} />
          if (w.status === 'triggered') return <TriggeredCard key={i} w={w} dispatch={dispatch} />
          return <PausedCard key={i} w={w} />
        })}
      </div>

      <footer className="watch-footer">
        {InfoIcon}
        {/* RocketRide GO recorded in docs/VERIFY.md (JSON schema clean, HTTP
            Request tool, OpenAI-Compatible node exposes a Base URL field ->
            TokenRouter). Each watch runs as a RocketRide pipeline: HTTP
            Request fetch + LLM compare, on a Render-cron-style interval. */}
        <span>Each watch is one RocketRide pipeline — fetch, compare, call</span>
      </footer>
    </div>
  )
}
