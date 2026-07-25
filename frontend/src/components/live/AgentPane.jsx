import { useEffect, useState } from 'react'

/**
 * One live agent card. Purely presentational — the ticking timer is local
 * display state seeded from agent.elapsed_s and never dispatches anything.
 */
function fmt(s) {
  const m = Math.floor(s / 60)
  const r = s % 60
  return `${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}`
}

const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
)

export default function AgentPane({ agent }) {
  const [secs, setSecs] = useState(agent.elapsed_s ?? 0)

  // re-seed whenever the stream reports authoritative elapsed time
  useEffect(() => {
    setSecs(agent.elapsed_s ?? 0)
  }, [agent.elapsed_s])

  // tick +1/s while working — display only
  useEffect(() => {
    if (agent.status !== 'working') return undefined
    const id = setInterval(() => setSecs((s) => s + 1), 1000)
    return () => clearInterval(id)
  }, [agent.status])

  const working = agent.status === 'working'
  const done = agent.status === 'done'
  const failed = agent.status === 'failed'
  const pct = agent.steps_total ? Math.min(100, (agent.step / agent.steps_total) * 100) : 0

  return (
    <section className="card live-pane">
      <div className="live-pane-head">
        <span className={`dot ${agent.status}${working ? ' pulse' : ''}`} />
        <span className="live-pane-name">{agent.id}</span>
        <span className="mono live-pane-target">{agent.target}</span>
        {done ? (
          <span className="live-pane-done">
            <CheckIcon /> done
          </span>
        ) : (
          <span className="mono live-pane-timer">{fmt(secs)}</span>
        )}
      </div>

      <div className="live-pane-body">
        {working && (
          <>
            <span className="skel" style={{ width: '85%' }} />
            <span className="skel" style={{ width: '60%' }} />
            <div className="live-stepline" key={agent.line}>{agent.line}</div>
          </>
        )}
        {done && (
          <>
            <div className="live-pane-line">{agent.line}</div>
            {agent.summary_lines?.note && (
              <div className="live-pane-note">{agent.summary_lines.note}</div>
            )}
          </>
        )}
        {failed && <div className="live-pane-fail">{agent.line}</div>}
        {agent.screenshot && (
          <img className="live-shot" src={agent.screenshot} alt={`${agent.id} screenshot`} />
        )}
      </div>

      <div className="live-pane-foot">
        <div className="bar">
          <i
            className={working ? 'working' : ''}
            style={{ width: `${pct}%`, background: failed ? 'var(--failed)' : undefined }}
          />
        </div>
        <span className="mono">step {agent.step}/{agent.steps_total}</span>
      </div>
    </section>
  )
}
