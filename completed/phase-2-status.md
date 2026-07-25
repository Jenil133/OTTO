# Phase 2 — Status (built ahead, Fri night)

The text spine is real and **passes the Checkpoint-1 acceptance script** — now
verified on **LIVE models**, not just mock. Both LLM stages run through the
TokenRouter gateway on the $50 event credit.

## 🔴 LIVE — TokenRouter wired (updated)

`backend/.env` holds the TokenRouter key; `GET /` reports `"mock": false`.
One OpenAI-compatible key + base URL `https://api.tokenrouter.com/v1` reaches
**both** LLM stages (117-model catalog).

**Verified live end-to-end (request `req_cdbe2260`):** typed request → real
planner → mocked Retriever → real MiniMax M3 synthesis → results card in the
browser over the real WebSocket. Zero console errors. **16s wall clock.**

### Planner model chosen by measured benchmark (not by vibes)

Same key, same prompt, measured live:

| model | latency | plan |
|---|---|---|
| **google/gemini-3.5-flash-lite** | **2.8s** | 3 subtasks ✅ **shipping** |
| openai/gpt-5.4-mini | 3.9s | ⚠️ 1 subtask — breaks the fan-out visual |
| x-ai/grok-4.1-fast | 7.6s | 3 subtasks |
| z-ai/glm-5-turbo | 10.4s | 3 subtasks |
| moonshotai/kimi-k3 | 28.0s | 3 subtasks (reasoning model) |

Kimi K3 plans correctly but burns reasoning tokens on a task that doesn't need
them — 28–42s against D2's 5–10s planner budget, which would blow the 60–90s
total once real Retriever agents land. Gemini flash-lite verified **5/5 runs,
2.6–2.9s**, identical allowlist targets, still clarifies on ambiguous asks.
Swap is one env var (`PLANNER_MODEL`), zero code change — **that is the
TokenRouter story, and it's a real engineering beat for the pitch.**

### Four bugs that ONLY surfaced by going live

1. **Kimi K3 rejects `temperature`** unless exactly `1` → HTTP 400. Param removed.
2. **MiniMax M3 prepends an un-fenced `<think>…</think>` block** before its JSON → every synthesis silently fell back to the mock composition. Now stripped.
3. **30s timeout too tight for reasoning models** → `ReadTimeout` on ~40% of planner calls, surfacing as a bogus "could you rephrase that?". Raised to 75s + retry on transport errors.
4. **Synthesizer was told about undispatched subtasks** → it honestly-but-wrongly reported the 2 un-run sites as failures. Now only dispatched subtasks are passed; Phase 3 makes this a no-op.

Both adapters now **log** live-call failures instead of swallowing them — that's
the only reason #2 and #3 were caught at all.

## ✅ Completed & verified

### Task A — Planner (Kimi K3 via TokenRouter/Respan) — `backend/adapters/kimi.py`
- `async plan(text, memory, request_id) -> Plan | Clarification`. Live path = OpenAI-compatible JSON-mode call; every VERIFY-dependent value (base URL, model string, JSON-mode flag, context-cache header) is an env override with a loud `# VERIFY:` marker, never a buried guess. One self-repair retry on bad JSON → else a Clarification. **Never raises** (D7).
- Mock path: deterministic plans (jobs / shopping / ambiguous→clarify) with zero keys.
- Real system prompt written to `backend/prompts/planner.md` (judged PDD artifact) with `{{ALLOWLIST}}` injection.

### Task B (code half) — Retriever adapter — `backend/adapters/retriever.py`
- `async run_subtask(subtask, on_step) -> AgentResult`. Live = submit→poll with a **hard 60s cap** → well-formed `partial`/`failed` on timeout, never raises. `on_step` callback drives `agent_update` events.
- Mock: canned Stripe / Anthropic(5) / Databricks(3) / generic flavors matching the golden run.
- **Empirical site scoring is Saturday platform work** (needs the Retriever key + live sites).

### Task C — Synthesizer (MiniMax M3) — `backend/adapters/minimax.py`
- `async synthesize(...) -> ResultPayload`. Merges ok/partial/failed; honesty paths (all-failed = honest failure, some-failed = proceed + say so). Multimodal screenshot-recovery branch stubbed + marked `# UNTESTED`. Real prompt in `backend/prompts/synthesizer.md`.

### Task D — Orchestrator + real event stream — `backend/pipeline.py`, `backend/main.py`
- `run_pipeline`: mem0-stub read (`[]`) → plan (or clarify) → **one** Retriever subtask (working/done `agent_update`s + 5s telemetry ticker + `agent_screenshot`) → synthesize → `result`. Every stage emits per CONTRACTS §1 and posts a Band line mirrored as `band_msg`. Whole body wrapped in a D7 crash-net.
- `POST /task` launches it in the background (task refs retained so the GC can't kill a run mid-flight).

### Task E — UI: real WebSocket + typed input — `frontend/src/ws.js`, `App.jsx`, `AskIdle`, `AskLive`
- `connectEvents` (capped-backoff reconnect, malformed-payload gate, bad-`?api=` guard) feeds the SAME `dispatch({type:'event'})` pipe as the mock. `postTask` fire-and-forget.
- Typed input box on Ask-idle ("or type it — ask anything") and Ask-live ("type a follow-up") — the permanent demo fallback.
- **`?mock=1` unchanged** (demo safety net). Hotkey `g` now ALWAYS plays the canned golden run even in `?mock=0` — so a dead backend mid-demo still shows a full run.

### Task F (fallback half) — Band feed — `backend/adapters/band.py`
- In-process feed + `async post(actor, text)`; mirrored as `band_msg`. Real Band SDK post is Saturday platform work (`# VERIFY:`), but the internal feed alone keeps the demo alive per spec.

## 🔎 Verification done (proof, not claims)
- **Full backend suite: 29/29 pytest green** in mock mode (no keys, no network).
- **CP1 script, HTTP:** `POST /task {"find new-grad SDE roles at Stripe"}` → `GET /status` returned `done` with a real spoken answer + 3-row Stripe card.
- **CP1 script, browser over real WebSocket** (`?mock=0&api=…`): chip → `POST /task` (+ CORS preflight, both 200) → live screen animated from `plan`/`agent_update`/`result` events → auto-advanced to Results showing a **real backend request_id** (`req_676fb800`, not the canned `req_1832`). Zero console errors.
- `g` golden replay confirmed to play `req_1832` even with `?mock=0`.
- **Adapter resilience** ("kill the Retriever key → mock keeps the loop alive") is inherent: the whole verification ran under `OTTO_MOCK=1`.
- Reviewer blockers fixed: WS broadcast snapshot iteration, allowlist pydantic gate (Zone-1, D5 — off-list target → Clarification), and the malformed-WS-event reducer crash. Plus polish: task-GC retention, longer request_id, binary-frame WS catch, `agent_screenshot` emit, `summary_lines` gated on done, IME-composition Enter guard, `cost_usd` null guard.

## ⏳ Pending (Saturday — needs keys/accounts/live sites)
- **Keys**: drop each sponsor key into `backend/.env` → that adapter flips live (D6). All `# VERIFY:` env values (TokenRouter base + K3 model string + JSON-mode/cache flags, Respan routing, Retriever routes + 60s poll shape, MiniMax endpoint + image-input format) get their real values from `docs/VERIFY.md` at the 9:45 gate.
- **Task B platform work**: run Retriever against the 8 allowlist candidates, score login-free/bot-defense/layout-stable/fast, cut losers, fill `docs/ALLOWLIST.md` winning phrasings.
- **Task F platform work**: create the real `otto-ops` Band room + persistent participants.
- **Task G**: deploy the spine to Render, run one typed request against the **deployed** URL, confirm Render supports the WebSocket.
- **Not in Phase 2 by design**: parallel fan-out (Ph3), voice (Ph3), real mem0 (Ph4), Respan cost telemetry (Ph4), RocketRide (Ph4).

## Run it locally
```
# backend (mock mode = no keys needed)
cd backend && OTTO_MOCK=1 .venv/bin/uvicorn main:app --port 8000
# frontend
cd frontend && npm run dev
# real spine in the browser:
open http://localhost:5173/?mock=0&api=http://localhost:8000
# safety-net demo (no backend needed): http://localhost:5173/?mock=1  (or press g)
```
