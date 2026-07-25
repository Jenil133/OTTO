/**
 * OTTO — real event stream client (Phase 2 · Task E).
 * Thin adapter over WS /events + POST /task (docs/CONTRACTS.md §1 + §6).
 * Every WS message goes through the SAME pipe as mockRun.js:
 *   dispatch({ type: 'event', event })
 * Unknown / malformed events are logged, never crash the UI (D4).
 *
 * Backend base resolution order: ?api=<origin> query override, then the
 * Vite build-time env var VITE_API_BASE (set as a Render Static Site env
 * var so the deployed frontend finds the deployed backend with no query
 * param), then localhost for local dev.
 */

export function apiBase() {
  return (
    new URLSearchParams(window.location.search).get('api') ??
    import.meta.env.VITE_API_BASE ??
    'http://localhost:8000'
  )
}

/**
 * Open WS /events and feed events into the reducer.
 * Auto-reconnects with capped backoff (1s, 2s, 4s… max 10s).
 * Returns a cleanup fn that closes the socket and stops reconnecting.
 */
export function connectEvents(dispatch, { base = apiBase() } = {}) {
  let ws = null
  let stopped = false
  let retryMs = 1000
  let retryTimer = null

  const scheduleRetry = () => {
    if (stopped) return
    retryTimer = setTimeout(open, retryMs)
    retryMs = Math.min(retryMs * 2, 10000)
  }

  const open = () => {
    if (stopped) return
    try {
      ws = new WebSocket(base.replace(/^http/, 'ws') + '/events')
    } catch (err) {
      // Garbage ?api= (e.g. missing protocol) throws synchronously — don't let
      // it escape connectEvents and break App mount; just back off and retry.
      console.warn('[ws] bad api base, retrying:', err)
      scheduleRetry()
      return
    }

    ws.onopen = () => {
      retryMs = 1000 // reset backoff on a good connection
    }

    ws.onmessage = (msg) => {
      let event
      try {
        event = JSON.parse(msg.data)
      } catch {
        console.warn('[ws] unparseable event, ignored:', msg.data)
        return
      }
      // Shape gate: a known type with a non-object payload would crash the
      // reducer (which reads event.payload.*). Drop it here (D4: never crash).
      if (!event || typeof event !== 'object' || !event.payload || typeof event.payload !== 'object') {
        console.warn('[ws] malformed event, ignored:', event)
        return
      }
      dispatch({ type: 'event', event })
    }

    ws.onerror = () => {
      // triggers onclose → reconnect path
      try { ws.close() } catch { /* already closed */ }
    }

    ws.onclose = () => {
      scheduleRetry()
    }
  }

  open()

  return () => {
    stopped = true
    clearTimeout(retryTimer)
    try { ws?.close() } catch { /* already closed */ }
  }
}

/**
 * POST /task { text } → { request_id, status } (or null on network error —
 * the UI just shows nothing new; run state arrives via the plan event).
 */
export async function postTask(text, { base = apiBase() } = {}) {
  try {
    const res = await fetch(base + '/task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
    return await res.json()
  } catch (err) {
    console.warn('[ws] POST /task failed:', err)
    return null
  }
}
