import './navrail.css'

const ICONS = {
  ask: (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="2.5" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0" /><line x1="12" y1="18" x2="12" y2="21.5" />
    </svg>
  ),
  runs: (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15.5 14" />
    </svg>
  ),
  watches: (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12z" /><circle cx="12" cy="12" r="2.6" />
    </svg>
  ),
  memory: (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 4a4 4 0 0 0-4 4v.5A3.5 3.5 0 0 0 5 12a3.5 3.5 0 0 0 3 3.5V16a4 4 0 0 0 8 0v-.5a3.5 3.5 0 0 0 3-3.5 3.5 3.5 0 0 0-3-3.5V8a4 4 0 0 0-4-4z" />
      <line x1="12" y1="4" x2="12" y2="20" />
    </svg>
  ),
  connect: (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 12h6" /><path d="M9.5 7H7a5 5 0 0 0 0 10h2.5" /><path d="M14.5 7H17a5 5 0 0 1 0 10h-2.5" />
    </svg>
  ),
}

const ITEMS = [
  { key: 'ask', label: 'Ask', screen: 'ask' },
  { key: 'runs', label: 'Runs', screen: 'results' },
  { key: 'watches', label: 'Watches', screen: 'watches' },
  { key: 'memory', label: 'Memory', screen: 'memory' },
  { key: 'connect', label: 'Connect', screen: 'connect' },
]

export default function NavRail({ screen, onNavigate }) {
  return (
    <nav className="navrail">
      <div className="navrail-brand">
        <span className="navrail-orb" />
        <span className="navrail-name">otto</span>
      </div>
      <div className="navrail-items">
        {ITEMS.map(it => {
          const active = it.screen === screen || (it.key === 'ask' && screen === 'live')
          return (
            <button
              key={it.key}
              className={`navrail-item${active ? ' active' : ''}`}
              onClick={() => onNavigate(it.screen)}
            >
              {ICONS[it.key]}
              <span>{it.label}</span>
            </button>
          )
        })}
      </div>
      <div className="navrail-foot">
        <span className="navrail-demo-dot" />
        <span>demo</span>
      </div>
    </nav>
  )
}
