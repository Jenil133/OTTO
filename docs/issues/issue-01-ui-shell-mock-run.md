# Build the Otto UI shell with a mock event engine and golden-run replay

**Route:** pdd-generate · **Phase:** 1 · **Owner:** Person 1 (shell + screens) + Person 2 (mock engine + contract freeze) · **Status: DONE (retroactive)**

## Goal

The entire Otto UI renders a believable ~62s three-agent run from a scripted event stream with **zero backend** — and that same stream contract is frozen so the real WebSocket can slot in behind it unchanged.

## Acceptance criteria

- **Given** the app at `?mock=1`, **when** a suggestion chip is clicked, **then** Ask-live animates end to end — plan ack in the transcript, three `<AgentPane>`s stepping `x/6` with progress bars, Band feed scrolling, telemetry chip ticking — and auto-advances to Results with a populated card. Zero console errors.
- **Given** any screen with focus outside an input, **when** hotkey `g` is pressed, **then** the golden run (`req_1832`) replays through the same `dispatch({type:'event'})` pipe.
- **Given** an event with an unknown `type` on the stream, **when** it is dispatched, **then** the UI logs and ignores it — never crashes (CONTRACTS.md §1 rule).
- **Given** `?speed=4`, **when** the mock run plays, **then** the whole timeline plays at 4× (rehearsal mode).
- **Given** the Results screen, **when** Export CSV is clicked, **then** a client-side CSV of the card downloads.

## Must not

- No component may fetch its own data — the UI renders ONLY from the one event stream (D4).
- No field name may drift from `docs/CONTRACTS.md` §1; `frontend/src/events.js` is its mirror.
- The mock stream must stay byte-compatible with the future `WS /events` stream — it doubles as the demo-night fallback (D7).

## Evidence

- `completed/phase-1-status.md`: Tasks A–D verified in browser, "Zero console errors"; Watches + Connect screens shipped as bonus.
- `frontend/src/mockRun.js`: scripted timeline — 3-subtask plan `req_1832`, agent 2 done at 41s with 5 roles, screenshot event, 5s telemetry ticks, result, memory beat.
- `docs/CONTRACTS.md` frozen (all 7 event types + Plan/AgentResult/mem0/Band shapes); `frontend/src/store.js` reduces every §1 type.
- `frontend/src/App.jsx`: `?mock=1` default, `?speed=N`, hotkey `g` wired.

## Validation

```
cd frontend && npx vite build          # passes (verified)
cd frontend && npm run dev             # then open:
open http://localhost:5173/?mock=1     # full mock run
# press g anywhere → golden replay · add &speed=4 for fast playback
```

## Done when

- [x] Every acceptance criterion above observed in the browser.
- [x] Negative path covered: unknown event type ignored, malformed payload never crashes the reducer.
- [x] Issue, code, and `docs/CONTRACTS.md` agree — contract freeze announced.
- [x] No secrets anywhere (frontend has no keys by design).
- [x] `npx vite build` passes.
- [x] Exact demo flow (`?mock=1` → chip → Results, then `g`) works manually.
- [x] Recorded in `completed/phase-1-status.md`; Saturday PR links here for checkup.
