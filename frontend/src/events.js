/**
 * OTTO — FROZEN EVENT CONTRACT (Phase 1 · Task D)
 * ================================================
 * This file + docs/CONTRACTS.md are the freeze. All four builders code
 * against these shapes. Nobody changes them after Sat 9:45 without telling
 * the whole room out loud.
 *
 * ONE typed stream (WS /events in production, mockRun.js in ?mock=1):
 *
 *   { "type": <EVENT_TYPES>, "payload": {...}, "ts": <epoch ms> }
 *
 * Payload shapes per type:
 *
 * plan             { request_id, spoken_ack, recall?: [string],
 *                    subtasks: [{ id, target, title, steps_total }] }
 *                  // recall = mem0 prefs read before planning → "otto knows" pills
 * band_msg         { actor, text }                       // actor: "plan"|"ag01".."ag03"|"synth"|"respan"|"mem0"
 * agent_update     { subtask_id, status: "working"|"done"|"failed",
 *                    step, steps_total, line, elapsed_s, summary_lines? }
 * agent_screenshot { subtask_id, ref }                   // ref: url or data-uri
 * telemetry        { cost_usd, elapsed_s, agents, gateway }   // gateway: "respan"
 * result           { request_id, status: "ok"|"partial"|"failed",
 *                    spoken, card: { columns, rows: [{ company, role, location, fit, url }] },
 *                    sources: [string], elapsed_s, cost_usd, agents }
 * memory_update    { kind: "preference"|"alias"|"fact", text, request_id }
 *
 * AgentResult (backend internal, spec §5 — mirrored here for reference):
 *   { subtask_id, status: "ok"|"partial"|"failed", data,
 *     screenshot_ref, steps_log, elapsed_s }
 *
 * RULES (architecture D4):
 *  · UI renders ONLY from this stream — no component fetches anything itself.
 *  · Unknown event types are logged, never crash the UI.
 */

export const EVENT_TYPES = [
  'plan',
  'band_msg',
  'agent_update',
  'agent_screenshot',
  'result',
  'telemetry',
  'memory_update',
]

export function makeEvent(type, payload, ts) {
  if (!EVENT_TYPES.includes(type)) {
    console.warn('[events] unknown event type:', type)
  }
  return { type, payload, ts: ts ?? 0 }
}

/** Guard used by the reducer — unknown types log + no-op, never crash. */
export function isKnownEvent(evt) {
  return evt && typeof evt === 'object' && EVENT_TYPES.includes(evt.type)
}
