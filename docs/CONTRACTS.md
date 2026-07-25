# OTTO — FROZEN CONTRACTS (Phase 1 · Task D)

**Status: FROZEN.** All four builders code against this file. Nobody changes a
shape after Sat 9:45 without telling all four people out loud.
Mirror: `frontend/src/events.js`. On any conflict, THIS file wins for field
names; `architecture-diagrams.md` wins for flow.

---

## 1 · WebSocket event (the ONE stream — D4)

Every message on `WS /events` (and every mock event from `mockRun.js`):

```json
{ "type": "plan | band_msg | agent_update | agent_screenshot | result | telemetry | memory_update",
  "payload": { },
  "ts": 1753500000000 }
```

Rules:
- UI renders ONLY from this stream. No component fetches anything itself.
- Unknown `type` → log + ignore. Never crash the UI.
- Mock engine (`?mock=1`) replays a recorded stream through the same pipe →
  identical UI. Golden-run hotkey: `g`.

### Payloads

**plan**
```json
{ "request_id": "req_1832",
  "spoken_ack": "On it — three agents out. Bay Area only, like last time.",
  "recall": ["new-grad", "bay area"],
  "subtasks": [
    { "id": "st_1", "target": "stripe.com/jobs", "title": "Stripe new-grad SWE roles", "steps_total": 6 }
  ] }
```
Max 3 subtasks · allowlist-only targets · read-only actions.
`recall` (optional) = mem0 preferences read before planning → feeds the
"otto knows" pills from t≈1s.

**band_msg**
```json
{ "actor": "plan | ag01 | ag02 | ag03 | synth | respan | mem0", "text": "5 roles · done · 41s" }
```

**agent_update**
```json
{ "subtask_id": "st_2", "status": "working | done | failed",
  "step": 4, "steps_total": 6, "line": "extracting roles → 3 matched",
  "elapsed_s": 14,
  "summary_lines": { "roles": 5, "newgrad": 2, "note": "2 flagged new-grad friendly" } }
```
`summary_lines` present only on `done`.

**agent_screenshot**
```json
{ "subtask_id": "st_3", "ref": "<url or data-uri>" }
```

**telemetry** (every ~5s)
```json
{ "cost_usd": 0.11, "elapsed_s": 48, "agents": 3, "gateway": "respan" }
```

**result**
```json
{ "request_id": "req_1832", "status": "ok | partial | failed",
  "spoken": "Found 12 roles… Want the links?",
  "card": {
    "columns": ["company", "role", "location", "fit"],
    "rows": [ { "company": "Stripe", "role": "SWE, new grad", "location": "SF", "fit": "new-grad", "url": "https://stripe.com/jobs" } ]
  },
  "sources": ["stripe.com/jobs", "anthropic.com/careers"],
  "elapsed_s": 62, "cost_usd": 0.11, "agents": 3 }
```
`fit` is a free string rendered as a pill; `"new-grad"` renders accent, others muted.

**memory_update**
```json
{ "kind": "preference | alias | fact", "text": "Prefers new-grad level roles",
  "pill": "new-grad", "request_id": "req_1832" }
```
`pill` optional — short form for the "otto knows" rail; defaults to `text`.

---

## 2 · Plan JSON (Planner → Dispatcher, spec §5)

Same object as the `plan` payload above. Constraints enforced by pydantic in
Phase 2: ≤3 subtasks, every `target` on `docs/ALLOWLIST.md`, read-only, each
subtask carries success criteria in `title`.

## 3 · AgentResult (Retriever adapter → Synthesizer)

```json
{ "subtask_id": "st_2", "status": "ok | partial | failed",
  "data": { "roles": [ { "company": "…", "role": "…", "location": "…", "fit": "…", "url": "…" } ] },
  "screenshot_ref": "<url or null>",
  "steps_log": ["opened page", "dismissed cookie banner"],
  "elapsed_s": 41 }
```

## 4 · mem0 entry

```json
{ "kind": "preference | alias | fact", "text": "Bay Area or remote only",
  "request_id": "req_1832", "used": 2 }
```

## 5 · Band message

```json
{ "room": "otto-ops", "actor": "planner | webagent-1 | webagent-2 | webagent-3 | synthesizer",
  "text": "dispatching ×3", "ts": 1753500000000 }
```
Mirrored into the UI feed rail as `band_msg` events (actor shortened to `ag01…`).

---

## 6 · HTTP surface (backend skeleton, Phase 1 · Task E)

| Route | In | Out |
|---|---|---|
| `POST /task` | `{ "text": "…" }` | `{ "request_id": "req_…", "status": "accepted" }` |
| `WS /events` | — | stream of §1 events |
| `GET /status/:id` | — | `{ "request_id", "status": "running \| done \| failed", "result": <result payload or null> }` |
| `POST /watch` | `{ "url", "condition", "contact_mode" }` | `{ "watch_id", "status": "watching" }` |
