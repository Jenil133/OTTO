import './connect.css'

/**
 * Connect — scoped keys, revocable anytime, every action logged.
 * Static screen (Phase 1). Renders ONLY from state.connections.
 */

const MailIcon = (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <polyline points="3 7 12 13 21 7" />
  </svg>
)

const CheckIcon = (
  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor"
    strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="20 6 9 17 4 12" />
  </svg>
)

const CalendarIcon = (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="3" y="4.5" width="18" height="16" rx="2" />
    <line x1="8" y1="2.5" x2="8" y2="6.5" />
    <line x1="16" y1="2.5" x2="16" y2="6.5" />
    <line x1="3" y1="9.5" x2="21" y2="9.5" />
  </svg>
)

const NotionIcon = (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M14 2.5H6a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8.5z" />
    <polyline points="14 2.5 14 8.5 20 8.5" />
    <line x1="8.5" y1="13" x2="15.5" y2="13" />
    <line x1="8.5" y1="16.5" x2="13" y2="16.5" />
  </svg>
)

const ZoomIcon = (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="2.5" y="7" width="13" height="10" rx="2" />
    <path d="M15.5 13.5l6 3.5v-10l-6 3.5" />
  </svg>
)

const LockIcon = (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="4.5" y="10.5" width="15" height="10" rx="2" />
    <path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" />
  </svg>
)

const LoopIcon = (
  <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="23 4 23 10 17 10" />
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
  </svg>
)

const AVAILABLE_ICONS = {
  Calendar: CalendarIcon,
  Notion: NotionIcon,
  Zoom: ZoomIcon,
}

export default function Connect({ state }) {
  const { connected = [], available = [] } = state.connections ?? {}

  return (
    <div className="conn-page">
      <header className="conn-head">
        <h1 className="conn-title">Connections</h1>
        <span className="conn-sub">· scoped keys, revocable anytime, every action logged</span>
      </header>

      <div className="mono conn-label">connected</div>
      {connected.map((c) => (
        <div key={c.name} className="card conn-gmail">
          <span className="conn-gmail-icon">{MailIcon}</span>
          <div className="conn-gmail-body">
            <div className="conn-gmail-name">
              <span>{c.name}</span>
              <span className="conn-gmail-check">{CheckIcon}</span>
              <span className="conn-gmail-mail">{c.account}</span>
            </div>
            <div className="conn-scopes">
              {c.scopes.map((s) => (
                <span key={s} className="pill muted conn-scope">{s}</span>
              ))}
            </div>
          </div>
          <div className="conn-gmail-side">
            <span className="mono">{c.actions_logged} actions logged</span>
            <button className="btn ghost conn-revoke">revoke</button>
          </div>
        </div>
      ))}

      <div className="mono conn-label">available · one handshake each</div>
      <div className="conn-grid">
        {available.map((name) => (
          <div key={name} className="card conn-avail">
            <span className="conn-avail-icon">{AVAILABLE_ICONS[name] ?? NotionIcon}</span>
            <span className="conn-avail-name">{name}</span>
            <button className="conn-connect-btn">connect</button>
          </div>
        ))}
      </div>

      <div className="mono conn-label">no door</div>
      <div className="card conn-nodoor">
        <span className="conn-nodoor-icon">{LockIcon}</span>
        <span className="conn-nodoor-text">
          LinkedIn and similar walled gardens — no public API, blocks automation.
          Otto doesn&rsquo;t pretend otherwise.
        </span>
      </div>

      <footer className="mono conn-audit">
        {LoopIcon}
        <span>audit trail → every action mirrors to the band room</span>
      </footer>
    </div>
  )
}
