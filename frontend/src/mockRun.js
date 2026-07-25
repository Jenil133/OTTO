/**
 * OTTO — mock event engine (Phase 1 · Task D).
 * Replays a scripted ~60s job-hunt run through the SAME pipe the real
 * WS /events will use. This IS the golden-run / cached-fallback foundation
 * for demo night (architecture D4 + D7).
 *
 * Usage:
 *   const stop = playMockRun(dispatch, { speed: 1 })
 *   stop() to cancel.
 *
 * ?mock=1  — app uses this engine instead of the WS
 * ?speed=4 — playback speed multiplier (dev / rehearsal)
 * hotkey g — golden-run replay (wired in App.jsx)
 */
import { makeEvent } from './events.js'

export const MOCK_USER_TEXT = 'Find new-grad SDE roles at Stripe, Anthropic, Databricks'

const shot = (label) =>
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360">
       <rect width="640" height="360" fill="#0A0E12"/>
       <rect x="24" y="24" width="592" height="42" rx="6" fill="#11161C" stroke="#232B34"/>
       <rect x="24" y="86" width="380" height="14" rx="7" fill="#232B34"/>
       <rect x="24" y="116" width="520" height="10" rx="5" fill="#232B34"/>
       <rect x="24" y="138" width="470" height="10" rx="5" fill="#232B34"/>
       <rect x="24" y="176" width="592" height="64" rx="8" fill="#11161C" stroke="#2DD4A7"/>
       <rect x="44" y="198" width="300" height="12" rx="6" fill="#2DD4A7" opacity="0.7"/>
       <rect x="24" y="256" width="592" height="64" rx="8" fill="#11161C" stroke="#232B34"/>
       <rect x="44" y="278" width="260" height="12" rx="6" fill="#232B34"/>
       <text x="24" y="350" fill="#8A94A0" font-family="monospace" font-size="12">${label}</text>
     </svg>`,
  )

/* Timeline: [seconds, type, payload]. Agent 2 finishes at 41s with 5 roles;
   agent 3 is slower. Telemetry ticks every 5s. Total ≈ 62s. */
const T = [
  [0.4,  'band_msg', { actor: 'plan', text: '3 subtasks' }],

  [1.2,  'plan', {
    request_id: 'req_1832',
    spoken_ack: 'On it — three agents out. Bay Area only, like last time.',
    recall: ['new-grad', 'bay area'],
    subtasks: [
      { id: 'st_1', target: 'stripe.com/jobs',        title: 'Stripe new-grad SWE roles',     steps_total: 6 },
      { id: 'st_2', target: 'anthropic.com/careers',  title: 'Anthropic early-career roles',  steps_total: 6 },
      { id: 'st_3', target: 'databricks.com/careers', title: 'Databricks new-grad SWE roles', steps_total: 6 },
    ],
  }],

  [1.6,  'band_msg', { actor: 'plan', text: 'allowlist ok · read-only · dispatching ×3' }],

  /* -------- fan-out begins -------- */
  [2.2,  'agent_update', { subtask_id: 'st_1', status: 'working', step: 1, steps_total: 6, line: 'opening stripe.com/jobs', elapsed_s: 1 }],
  [2.6,  'agent_update', { subtask_id: 'st_2', status: 'working', step: 1, steps_total: 6, line: 'opening anthropic.com/careers', elapsed_s: 1 }],
  [3.0,  'agent_update', { subtask_id: 'st_3', status: 'working', step: 1, steps_total: 6, line: 'opening databricks.com/careers', elapsed_s: 1 }],
  [3.4,  'band_msg', { actor: 'respan', text: 'route kimi-k3 · 1.9s · $0.01' }],

  [5.0,  'telemetry', { cost_usd: 0.02, elapsed_s: 5, agents: 3, gateway: 'respan' }],
  [5.5,  'agent_update', { subtask_id: 'st_1', status: 'working', step: 2, steps_total: 6, line: 'cookie banner dismissed', elapsed_s: 4 }],
  [6.2,  'agent_update', { subtask_id: 'st_2', status: 'working', step: 2, steps_total: 6, line: 'navigating to open roles', elapsed_s: 4 }],
  [7.0,  'agent_update', { subtask_id: 'st_3', status: 'working', step: 2, steps_total: 6, line: 'waiting on page load', elapsed_s: 4 }],
  [8.0,  'band_msg', { actor: 'ag02', text: 'careers index loaded' }],

  [10.0, 'telemetry', { cost_usd: 0.03, elapsed_s: 10, agents: 3, gateway: 'respan' }],
  [10.5, 'agent_update', { subtask_id: 'st_1', status: 'working', step: 3, steps_total: 6, line: 'filtering: engineering · university', elapsed_s: 9 }],
  [11.5, 'agent_update', { subtask_id: 'st_2', status: 'working', step: 3, steps_total: 6, line: 'scanning listings — page 1/2', elapsed_s: 9 }],
  [12.5, 'agent_update', { subtask_id: 'st_3', status: 'working', step: 2, steps_total: 6, line: 'scrolling listings', elapsed_s: 10 }],
  [13.0, 'band_msg', { actor: 'ag01', text: 'filters applied · 14 listings' }],

  [15.0, 'telemetry', { cost_usd: 0.04, elapsed_s: 15, agents: 3, gateway: 'respan' }],
  [16.0, 'agent_update', { subtask_id: 'st_2', status: 'working', step: 4, steps_total: 6, line: 'extracting roles → 3 matched', elapsed_s: 14 }],
  [17.0, 'agent_update', { subtask_id: 'st_1', status: 'working', step: 3, steps_total: 6, line: 'reading role cards', elapsed_s: 15 }],
  [18.0, 'band_msg', { actor: 'ag02', text: 'extracting → 3 roles matched' }],
  [19.0, 'agent_update', { subtask_id: 'st_3', status: 'working', step: 3, steps_total: 6, line: 'careers page → engineering', elapsed_s: 16 }],

  [20.0, 'telemetry', { cost_usd: 0.05, elapsed_s: 20, agents: 3, gateway: 'respan' }],
  [21.0, 'agent_update', { subtask_id: 'st_1', status: 'working', step: 4, steps_total: 6, line: 'extracting → 3 roles matched', elapsed_s: 19 }],
  [22.5, 'agent_update', { subtask_id: 'st_2', status: 'working', step: 5, steps_total: 6, line: 'checking new-grad eligibility', elapsed_s: 20 }],
  [24.0, 'band_msg', { actor: 'ag01', text: 'step 4/6' }],

  [25.0, 'telemetry', { cost_usd: 0.06, elapsed_s: 25, agents: 3, gateway: 'respan' }],
  [26.0, 'agent_update', { subtask_id: 'st_3', status: 'working', step: 4, steps_total: 6, line: 'scrolling listings', elapsed_s: 23 }],
  [27.0, 'band_msg', { actor: 'ag03', text: 'scrolling' }],
  [28.0, 'agent_update', { subtask_id: 'st_1', status: 'working', step: 4, steps_total: 6, line: 'reading infra eng posting', elapsed_s: 26 }],

  [30.0, 'telemetry', { cost_usd: 0.07, elapsed_s: 30, agents: 3, gateway: 'respan' }],
  [31.0, 'agent_update', { subtask_id: 'st_2', status: 'working', step: 6, steps_total: 6, line: 'compiling summary', elapsed_s: 29 }],
  [33.0, 'agent_update', { subtask_id: 'st_1', status: 'working', step: 5, steps_total: 6, line: 'collecting apply links', elapsed_s: 31 }],

  [35.0, 'telemetry', { cost_usd: 0.08, elapsed_s: 35, agents: 3, gateway: 'respan' }],
  [35.5, 'agent_screenshot', { subtask_id: 'st_3', ref: shot('databricks.com/careers · step 4/6') }],
  [36.0, 'band_msg', { actor: 'ag03', text: 'screenshot captured' }],
  [37.0, 'agent_update', { subtask_id: 'st_3', status: 'working', step: 5, steps_total: 6, line: 'extracting → 1 role matched', elapsed_s: 34 }],

  [40.0, 'telemetry', { cost_usd: 0.09, elapsed_s: 40, agents: 3, gateway: 'respan' }],

  /* -------- agent 2 lands first (mockup beat) -------- */
  [41.0, 'agent_update', {
    subtask_id: 'st_2', status: 'done', step: 6, steps_total: 6,
    line: '5 roles extracted · 41s', elapsed_s: 41,
    summary_lines: { roles: 5, newgrad: 2, note: '2 flagged new-grad friendly' },
  }],
  [41.4, 'band_msg', { actor: 'ag02', text: '5 roles · done · 41s' }],

  [44.0, 'agent_update', { subtask_id: 'st_1', status: 'working', step: 5, steps_total: 6, line: 'verifying locations — SF', elapsed_s: 42 }],
  [45.0, 'telemetry', { cost_usd: 0.10, elapsed_s: 45, agents: 3, gateway: 'respan' }],
  [47.0, 'agent_update', { subtask_id: 'st_3', status: 'working', step: 5, steps_total: 6, line: 'checking Mountain View listing', elapsed_s: 44 }],

  /* -------- agent 1 lands -------- */
  [50.0, 'agent_update', {
    subtask_id: 'st_1', status: 'done', step: 6, steps_total: 6,
    line: '4 roles extracted · 48s', elapsed_s: 48,
    summary_lines: { roles: 4, newgrad: 2, note: '2 flagged new-grad friendly' },
  }],
  [50.4, 'band_msg', { actor: 'ag01', text: '4 roles · done · 48s' }],
  [50.8, 'telemetry', { cost_usd: 0.10, elapsed_s: 50, agents: 3, gateway: 'respan' }],

  /* -------- agent 3 lands last -------- */
  [55.0, 'agent_update', {
    subtask_id: 'st_3', status: 'done', step: 6, steps_total: 6,
    line: '3 roles extracted · 52s', elapsed_s: 52,
    summary_lines: { roles: 3, newgrad: 1, note: '1 flagged new-grad friendly' },
  }],
  [55.4, 'band_msg', { actor: 'ag03', text: '3 roles · done · 52s' }],
  [56.0, 'band_msg', { actor: 'synth', text: 'merging 3 results → minimax-m3' }],
  [57.0, 'band_msg', { actor: 'respan', text: 'route minimax-m3 · 4.2s · $0.01' }],

  /* -------- synthesize → speak -------- */
  [60.0, 'telemetry', { cost_usd: 0.11, elapsed_s: 60, agents: 3, gateway: 'respan' }],
  [61.5, 'result', {
    request_id: 'req_1832',
    status: 'ok',
    spoken:
      'Found 12 roles across the three companies — 5 are new-grad friendly. ' +
      'Stripe has two in SF, Anthropic two, Databricks one in Mountain View. Want the links?',
    card: {
      columns: ['company', 'role', 'location', 'fit'],
      rows: [
        { company: 'Stripe',     role: 'SWE, new grad',      location: 'SF',       fit: 'new-grad', url: 'https://stripe.com/jobs' },
        { company: 'Anthropic',  role: 'SWE, early career',  location: 'SF',       fit: 'new-grad', url: 'https://anthropic.com/careers' },
        { company: 'Databricks', role: 'SWE, new grad',      location: 'Mtn View', fit: 'new-grad', url: 'https://databricks.com/careers' },
        { company: 'Stripe',     role: 'Infrastructure eng', location: 'SF',       fit: 'mid',      url: 'https://stripe.com/jobs' },
        { company: 'Anthropic',  role: 'Applied AI',         location: 'SF',       fit: 'mid',      url: 'https://anthropic.com/careers' },
      ],
    },
    sources: ['stripe.com/jobs', 'anthropic.com/careers', 'databricks.com/careers'],
    elapsed_s: 62, cost_usd: 0.11, agents: 3,
  }],

  /* -------- memory beat (async, off critical path) -------- */
  [62.5, 'memory_update', { kind: 'preference', text: 'Prefers new-grad level roles', pill: 'new-grad', request_id: 'req_1832' }],
  [63.0, 'memory_update', { kind: 'preference', text: 'Bay Area or remote only', pill: 'bay area', request_id: 'req_1832' }],
  [63.2, 'memory_update', { kind: 'fact', text: 'Job hunting since July 2026', request_id: 'req_1832' }],
  [63.4, 'band_msg', { actor: 'mem0', text: 'wrote 2 prefs + 1 fact (async)' }],
]

/** Total scripted length in seconds (used for auto-advance to results). */
export const MOCK_RUN_LENGTH_S = 64

/**
 * Play the scripted run. Returns a cancel function.
 * Every event goes through dispatch({type:'event', event}) — the exact
 * interface the real WS client will use.
 */
export function playMockRun(dispatch, { speed = 1 } = {}) {
  const timers = T.map(([t, type, payload]) =>
    setTimeout(
      () => dispatch({ type: 'event', event: makeEvent(type, payload, Date.now()) }),
      (t * 1000) / speed,
    ),
  )
  const doneTimer = setTimeout(
    () => dispatch({ type: 'ui/run_complete' }),
    (MOCK_RUN_LENGTH_S * 1000) / speed,
  )
  return () => { timers.forEach(clearTimeout); clearTimeout(doneTimer) }
}
