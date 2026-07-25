/**
 * OTTO — single state object + reducer.
 * Every component renders from `state` via props. Nothing fetches inside
 * components (Phase 1 Task B rule). Stream events and UI actions both go
 * through this one reducer.
 *
 * dispatch({ type: 'event', event })          — stream event (mock or real WS)
 * dispatch({ type: 'ui/navigate', screen })   — 'ask'|'live'|'results'|'memory'|'watches'|'connect'
 * dispatch({ type: 'ui/start_run', text })    — user asked something (starts a run shell)
 * dispatch({ type: 'ui/orb', orb })           — 'idle'|'recording'|'processing'
 * dispatch({ type: 'ui/delete_know', text })  — remove an "otto knows" pill
 * dispatch({ type: 'ui/delete_memory', section, idx })
 * dispatch({ type: 'ui/run_complete' })       — auto-advance to results screen
 */
import { isKnownEvent } from './events.js'

export const initialState = {
  screen: 'ask',
  orb: 'idle', // 'idle' | 'recording' | 'processing'
  run: null,   // current / last run (shape below)
  memory: {
    preferences: [
      { text: 'Aisle seat on flights', request_id: 'req_1790', used: 4 },
      { text: 'Budget cap around $900 for flights', request_id: 'req_1790', used: 1 },
    ],
    aliases: [
      { text: '“my usual hotel” → Grand Kyoto', request_id: 'req_1671', used: 3 },
      { text: '“the team” → Ravi, Mei, Jordan', request_id: 'req_1702', used: 1 },
    ],
    facts: [],
  },
  watches: [
    {
      title: 'RTX 4070 drops under $200',
      target: 'gpuhub.com/rtx-4070', cadence: 'every 10 min',
      last_check: '2m ago', now: '$214', status: 'watching',
      note: 'will call you when it hits',
      history: [0, 0, 0, 0, 0, 0, 1],
    },
    {
      title: 'Coldplay tickets on sale',
      target: 'tixhub.com/coldplay-sf', cadence: 'checked 118× over 2 days',
      status: 'triggered', triggered_at: '14:32',
      note: 'Called you · answered in 41s · “grab two?”',
    },
    {
      title: 'Visa appointment slots · SF consulate',
      status: 'paused',
    },
  ],
  connections: {
    connected: [
      { name: 'Gmail', account: 'demo.otto@gmail.com', scopes: ['read', 'draft', 'send · off'], actions_logged: 12 },
    ],
    available: ['Calendar', 'Notion', 'Zoom'],
  },
}

function newRun(text) {
  return {
    id: null,
    status: 'planning', // 'planning'|'running'|'assembling'|'speaking'|'complete'
    started_at: Date.now(),
    user_text: text,
    transcript: [{ role: 'user', text }],
    agents: [],       // { id, subtask_id, target, status, step, steps_total, line, elapsed_s, summary_lines, screenshot }
    band: [],         // { actor, text, ts }
    knows: [],        // strings — "otto knows" pills
    telemetry: { cost_usd: 0, elapsed_s: 0, agents: 0, gateway: 'respan' },
    budget: { used_s: 0, cap_s: 90 },
    result: null,
    prefs_saved: 0,
  }
}

function applyEvent(state, evt) {
  if (!isKnownEvent(evt)) {
    console.warn('[store] unknown event, ignored:', evt)
    return state
  }
  const run = state.run
  const { payload: p } = evt

  switch (evt.type) {
    case 'plan': {
      if (!run) return state
      return {
        ...state,
        run: {
          ...run,
          id: p.request_id,
          status: 'running',
          transcript: [...run.transcript, { role: 'otto', text: p.spoken_ack }],
          agents: p.subtasks.map((s, i) => ({
            id: `agent 0${i + 1}`,
            subtask_id: s.id,
            target: s.target,
            title: s.title,
            status: 'working',
            step: 0,
            steps_total: s.steps_total,
            line: 'starting…',
            elapsed_s: 0,
            summary_lines: null,
            screenshot: null,
          })),
          knows: p.recall ?? run.knows,
          telemetry: { ...run.telemetry, agents: p.subtasks.length },
        },
      }
    }
    case 'band_msg': {
      if (!run) return state
      return { ...state, run: { ...run, band: [...run.band, { ...p, ts: evt.ts }] } }
    }
    case 'agent_update': {
      if (!run) return state
      return {
        ...state,
        run: {
          ...run,
          agents: run.agents.map(a =>
            a.subtask_id === p.subtask_id
              ? {
                  ...a,
                  status: p.status,
                  step: p.step ?? a.step,
                  steps_total: p.steps_total ?? a.steps_total,
                  line: p.line ?? a.line,
                  elapsed_s: p.elapsed_s ?? a.elapsed_s,
                  summary_lines: p.summary_lines ?? a.summary_lines,
                }
              : a,
          ),
        },
      }
    }
    case 'agent_screenshot': {
      if (!run) return state
      return {
        ...state,
        run: {
          ...run,
          agents: run.agents.map(a =>
            a.subtask_id === p.subtask_id ? { ...a, screenshot: p.ref } : a,
          ),
        },
      }
    }
    case 'telemetry': {
      if (!run) return state
      return {
        ...state,
        run: {
          ...run,
          telemetry: { ...run.telemetry, ...p },
          budget: { ...run.budget, used_s: p.elapsed_s ?? run.budget.used_s },
        },
      }
    }
    case 'result': {
      if (!run) return state
      return {
        ...state,
        run: {
          ...run,
          status: 'speaking',
          result: p,
          transcript: [...run.transcript, { role: 'otto', text: p.spoken }],
          telemetry: {
            ...run.telemetry,
            cost_usd: p.cost_usd ?? run.telemetry.cost_usd,
            elapsed_s: p.elapsed_s ?? run.telemetry.elapsed_s,
          },
          agents: run.agents.map(a =>
            a.status === 'working' ? { ...a, status: 'done' } : a,
          ),
        },
      }
    }
    case 'memory_update': {
      const sectionByKind = { preference: 'preferences', alias: 'aliases', fact: 'facts' }
      const section = sectionByKind[p.kind] ?? 'facts'
      const entry = { text: p.text, request_id: p.request_id, used: 1 }
      const next = {
        ...state,
        memory: { ...state.memory, [section]: [entry, ...state.memory[section]] },
      }
      if (run && p.kind === 'preference') {
        const pillText = p.pill ?? p.text
        next.run = {
          ...run,
          knows: run.knows.includes(pillText) ? run.knows : [...run.knows, pillText],
          prefs_saved: run.prefs_saved + 1,
        }
      }
      return next
    }
    default:
      return state
  }
}

export function reducer(state, action) {
  switch (action.type) {
    case 'event':
      return applyEvent(state, action.event)
    case 'ui/navigate':
      return { ...state, screen: action.screen }
    case 'ui/start_run':
      return { ...state, screen: 'live', orb: 'processing', run: newRun(action.text) }
    case 'ui/orb':
      return { ...state, orb: action.orb }
    case 'ui/run_complete':
      return {
        ...state,
        orb: 'idle',
        screen: 'results',
        run: state.run ? { ...state.run, status: 'complete' } : state.run,
      }
    case 'ui/delete_know':
      return state.run
        ? { ...state, run: { ...state.run, knows: state.run.knows.filter(k => k !== action.text) } }
        : state
    case 'ui/delete_memory': {
      const rows = state.memory[action.section].filter((_, i) => i !== action.idx)
      return { ...state, memory: { ...state.memory, [action.section]: rows } }
    }
    default:
      return state
  }
}

/** Footer status line — derived, not stored (keeps the contract minimal). */
export function footerStatus(run) {
  if (!run) return null
  if (run.status === 'speaking') return { left: 'Otto is speaking…', right: null }
  if (run.status === 'complete') return { left: 'run complete', right: null }
  const done = run.agents.filter(a => a.status === 'done').length
  const total = run.agents.length
  if (total > 0 && done === total)
    return { left: 'Results card assembling…', right: 'speaking in ~12s' }
  if (done > 0) {
    const doneAgents = run.agents.filter(a => a.status === 'done')
    const roles = doneAgents.reduce((n, a) => n + (a.summary_lines?.roles ?? 0), 0)
    const newgrad = doneAgents.reduce((n, a) => n + (a.summary_lines?.newgrad ?? 0), 0)
    return {
      left: `Results card assembling — ${roles} roles, ${newgrad} new-grad friendly`,
      right: 'speaking in ~12s',
    }
  }
  return { left: `${total} agents reading…`, right: null }
}
