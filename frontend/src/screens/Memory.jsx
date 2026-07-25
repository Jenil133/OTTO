import { useState } from 'react'
import { makeEvent } from '../events.js'
import './memory.css'

const SECTIONS = ['preferences', 'aliases', 'facts']

function MagnifierIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="7" />
      <line x1="16.5" y1="16.5" x2="21" y2="21" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 7h16" />
      <path d="M9 7V4.5A1.5 1.5 0 0 1 10.5 3h3A1.5 1.5 0 0 1 15 4.5V7" />
      <path d="M6.5 7l1 13a1.5 1.5 0 0 0 1.5 1.4h6a1.5 1.5 0 0 0 1.5-1.4l1-13" />
      <line x1="10" y1="11" x2="10" y2="17" />
      <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
  )
}

function InfoIcon() {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <line x1="12" y1="11" x2="12" y2="16.5" />
      <line x1="12" y1="7.5" x2="12" y2="7.6" />
    </svg>
  )
}

export default function Memory({ state, dispatch }) {
  const [query, setQuery] = useState('')
  const memory = state.memory

  const total = SECTIONS.reduce((n, s) => n + memory[s].length, 0)
  const q = query.trim().toLowerCase()

  const addMemory = () => {
    const text = window.prompt('remember what?')
    if (text && text.trim()) {
      dispatch({
        type: 'event',
        event: makeEvent(
          'memory_update',
          { kind: 'preference', text: text.trim(), request_id: 'manual' },
          Date.now(),
        ),
      })
    }
  }

  return (
    <div className="mem-wrap">
      <div className="mem-header">
        <div className="mem-title-row">
          <span className="mem-title">Memory</span>
          <span className="mem-subtitle">
            · {total} items · edits apply on the next request
          </span>
        </div>
        <label className="mem-search">
          <MagnifierIcon />
          <input
            className="mem-search-input"
            type="text"
            placeholder="search memory"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
      </div>

      {SECTIONS.map((section) => {
        const rows = memory[section]
          .map((row, idx) => ({ row, idx }))
          .filter(({ row }) => !q || row.text.toLowerCase().includes(q))

        return (
          <div key={section}>
            <div className="mem-section-label">{section}</div>
            <div className="card">
              {rows.length === 0 ? (
                <div className="mem-empty">nothing here</div>
              ) : (
                rows.map(({ row, idx }) => (
                  <div className="mem-row" key={`${row.request_id}-${idx}`}>
                    <span className="mem-row-text">{row.text}</span>
                    <span className="mem-row-meta">
                      <span className="mono">
                        {row.request_id} · used {row.used}×
                      </span>
                      <button
                        type="button"
                        className="mem-trash"
                        aria-label={`delete "${row.text}"`}
                        onClick={() =>
                          dispatch({ type: 'ui/delete_memory', section, idx })
                        }
                      >
                        <TrashIcon />
                      </button>
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )
      })}

      <div className="mem-footer">
        <span className="mem-hint">
          <InfoIcon />
          Delete one and Otto&rsquo;s next answer changes — try it live
        </span>
        <button type="button" className="btn ghost" onClick={addMemory}>
          + add memory
        </button>
      </div>
    </div>
  )
}
