import './results.css'
import { MOCK_USER_TEXT } from '../mockRun.js'

/* ---------- minimal inline icons (stroke, 14–16px) ---------- */
const ic = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

const IconBack = () => (
  <svg viewBox="0 0 24 24" width="15" height="15" {...ic}>
    <line x1="19" y1="12" x2="5" y2="12" />
    <polyline points="12 5 5 12 12 19" />
  </svg>
)

const IconCheck = () => (
  <svg viewBox="0 0 24 24" width="11" height="11" {...ic} strokeWidth="2.2">
    <polyline points="20 6 9 17 4 12" />
  </svg>
)

const IconSpeaker = () => (
  <svg viewBox="0 0 24 24" width="15" height="15" {...ic}>
    <path d="M11 5 6 9H3v6h3l5 4z" />
    <path d="M15.5 8.5a5 5 0 0 1 0 7" />
    <path d="M18.5 5.5a9 9 0 0 1 0 13" />
  </svg>
)

const IconPlay = () => (
  <svg viewBox="0 0 24 24" width="12" height="12" {...ic}>
    <polygon points="6 4 20 12 6 20 6 4" />
  </svg>
)

const IconExternal = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" {...ic}>
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </svg>
)

const IconMemory = () => (
  <svg viewBox="0 0 24 24" width="13" height="13" {...ic} strokeWidth="1.6">
    <rect x="7" y="7" width="10" height="10" rx="2" />
    <line x1="9" y1="4" x2="9" y2="7" />
    <line x1="15" y1="4" x2="15" y2="7" />
    <line x1="9" y1="17" x2="9" y2="20" />
    <line x1="15" y1="17" x2="15" y2="20" />
    <line x1="4" y1="9" x2="7" y2="9" />
    <line x1="4" y1="15" x2="7" y2="15" />
    <line x1="17" y1="9" x2="20" y2="9" />
    <line x1="17" y1="15" x2="20" y2="15" />
  </svg>
)

const IconMic = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" {...ic}>
    <rect x="9" y="2.5" width="6" height="11" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0" />
    <line x1="12" y1="18" x2="12" y2="21.5" />
  </svg>
)

const IconDownload = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" {...ic}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
)

/* ---------- csv helpers ---------- */
function csvField(v) {
  const s = String(v ?? '')
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

function exportCsv(res) {
  const { columns, rows } = res.card
  const lines = [
    columns.map(csvField).join(','),
    ...rows.map((r) => columns.map((c) => csvField(r[c])).join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `otto_${res.request_id}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

/* ---------- screen ---------- */
export default function Results({ state, dispatch, onRun }) {
  const run = state.run
  const res = run?.result

  if (!res) {
    return (
      <div className="res-empty">
        <div className="res-empty-title">no runs yet</div>
        <div className="mono">press g to play the golden run</div>
        <button className="btn ghost res-empty-btn" onClick={() => onRun(MOCK_USER_TEXT)}>
          <IconPlay />
          run mock
        </button>
      </div>
    )
  }

  const goAsk = () => dispatch({ type: 'ui/navigate', screen: 'ask' })

  return (
    <div className="res-page">
      {/* 1 · header */}
      <div className="res-head">
        <button className="res-back" onClick={goAsk} aria-label="back">
          <IconBack />
        </button>
        <span className="res-id">{res.request_id}</span>
        <span className="pill accent">
          <IconCheck />
          complete
        </span>
        <span className="mono res-head-meta">
          {res.elapsed_s}s · ${res.cost_usd.toFixed(2)} · {res.agents} agents
        </span>
      </div>

      {/* 2 · spoken answer */}
      <div className="res-spoken">
        <span className="res-spk-icon">
          <IconSpeaker />
        </span>
        <p className="res-spoken-text">&ldquo;{res.spoken}&rdquo;</p>
        <button className="btn ghost res-replay" type="button">
          <IconPlay />
          replay
        </button>
      </div>

      {/* 3 · results table */}
      <div className="card res-table">
        <div className="res-tr res-thead">
          {res.card.columns.map((c) => (
            <span key={c} className="res-th">{c}</span>
          ))}
          <span className="res-th" aria-hidden="true" />
        </div>
        {res.card.rows.map((row, i) => (
          <div className="res-tr" key={i}>
            <span className="res-cell res-company">{row.company}</span>
            <span className="res-cell">{row.role}</span>
            <span className="res-cell res-loc">{row.location}</span>
            <span>
              <span className={`pill res-fitpill ${row.fit === 'new-grad' ? 'accent' : 'muted'}`}>
                {row.fit}
              </span>
            </span>
            <a
              className="res-link"
              href={row.url}
              target="_blank"
              rel="noreferrer"
              aria-label={`open ${row.company} listing`}
            >
              <IconExternal />
            </a>
          </div>
        ))}
      </div>

      {/* 4 · sources / memory */}
      <div className="res-sub">
        <span className="mono">sources · {res.sources.join(' · ')}</span>
        <span className="res-mem">
          <IconMemory />
          {run.prefs_saved} preferences saved
        </span>
      </div>

      {/* 5 · actions */}
      <div className="res-actions">
        <button className="btn primary" onClick={goAsk}>
          <IconMic />
          Ask follow-up
        </button>
        <button className="btn ghost" onClick={() => exportCsv(res)}>
          <IconDownload />
          Export CSV
        </button>
      </div>
    </div>
  )
}
