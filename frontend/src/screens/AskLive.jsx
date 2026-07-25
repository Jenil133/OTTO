import { useState } from 'react'
import Orb from '../components/Orb.jsx'
import { footerStatus } from '../store.js'
import AgentPane from '../components/live/AgentPane.jsx'
import BandFeed from '../components/live/BandFeed.jsx'
import OttoKnows from '../components/live/OttoKnows.jsx'
import BudgetMeter from '../components/live/BudgetMeter.jsx'
import './asklive.css'

/**
 * Ask-live — the money screen (otto.run/live).
 * Renders ONLY from state.run; every update arrives via the event stream.
 */
export default function AskLive({ state, dispatch, onRun }) {
  const run = state.run
  const [followUp, setFollowUp] = useState('')

  const submitFollowUp = () => {
    const t = followUp.trim()
    if (!t) return
    onRun?.(t)
    setFollowUp('')
  }

  if (!run) {
    return (
      <div className="live-empty">
        <div className="live-empty-title">no live run</div>
        <div className="mono">press g for golden replay</div>
      </div>
    )
  }

  const t = run.telemetry
  const fs = footerStatus(run)

  return (
    <div className="live-root">
      {/* top bar */}
      <header className="live-topbar">
        <div className="live-brand">
          <span className="live-wordmark">otto</span>
          <span className="pill accent">
            {/* teal dot here = event stream connected, not run status */}
            <span className="dot done pulse" />
            live · {run.id ?? '…'}
          </span>
        </div>
        <div className="telemetry">
          {`$${(t.cost_usd ?? 0).toFixed(2)} · ${t.elapsed_s ?? 0}s · ${t.agents ?? 0} agents · ${t.gateway ?? ''}`}
        </div>
      </header>

      {/* 3-column grid */}
      <div className="live-grid">
        {/* left — transcript + orb */}
        <div className="live-col live-col-left">
          <div className="live-transcript">
            {run.transcript.map((m, i) => (
              <div
                key={i}
                className={`live-bubble ${m.role === 'otto' ? 'live-bubble-otto' : 'live-bubble-user'}`}
              >
                {m.text}
              </div>
            ))}
          </div>
          <div className="live-orbzone">
            <Orb mode={state.orb} size={76} label="hold to talk" />
          </div>
          <input
            type="text"
            className="live-input"
            value={followUp}
            placeholder="type a follow-up"
            onChange={(e) => setFollowUp(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.nativeEvent.isComposing) submitFollowUp() }}
          />
        </div>

        {/* center — agent panes */}
        <div className="live-col live-agents">
          {run.agents.map((a) => (
            <AgentPane key={a.subtask_id} agent={a} />
          ))}
        </div>

        {/* right rail */}
        <div className="live-col live-rail">
          <BandFeed band={run.band} />
          <OttoKnows knows={run.knows} dispatch={dispatch} />
          <BudgetMeter budget={run.budget} />
        </div>
      </div>

      {/* footer status line */}
      <footer className="live-footer">
        <span className="live-footer-left" key={fs?.left}>{fs?.left}</span>
        <span className="live-footer-right">{fs?.right}</span>
      </footer>
    </div>
  )
}
