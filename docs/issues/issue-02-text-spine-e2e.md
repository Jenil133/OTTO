# Run the text spine end-to-end over the real WebSocket

**Route:** pdd-change · **Phase:** 2 · **Owner:** Person 2 (planner/synth/orchestrator) + Person 1 (WS client) + Person 3 (Retriever adapter) · **Status: DONE (retroactive)**

## Goal

A typed request runs the whole spine — live planner → one Retriever subtask → live MiniMax synthesis → results card in the browser — over the real `WS /events`, with every failure path landing as an honest, well-formed result.

## Acceptance criteria

- **Given** the backend live via TokenRouter, **when** a request is typed in the UI (`?mock=0&api=…`), **then** §1 `plan` / `agent_update` / `result` events stream over `WS /events` and the results card renders with a real backend request id. **Observed live: `req_cdbe2260`, 16s wall clock, zero console errors** (real planner `google/gemini-3.5-flash-lite` → mock Retriever → real MiniMax-M3 synthesis).
- **Given** keyless mock mode, **when** `pytest tests/ -q` runs, **then** the full suite passes with no network. **Observed: 29/29 green at phase-2 close (suite has since grown — rerun for the live count).**
- **Given** an ambiguous ask, **when** planned, **then** a Clarification comes back as a `partial` result whose `spoken` is the question, and no `plan` event is emitted (`test_ambiguous_utterance_returns_clarification`, `test_clarification_path_partial_result_and_no_plan_event`).
- **Given** a planner hallucinating an off-allowlist target, **when** the plan validates, **then** pydantic's Zone-1 gate (`schemas.PlanSubtask.on_allowlist`) rejects it → clarification path, never a browser drive.
- **Given** every agent failed, **when** synthesized, **then** the result is an honest `failed` with **zero fabricated rows** (`test_all_failed_is_honest`).
- **Given** a dead backend, **when** `?mock=1` or hotkey `g` is used, **then** the golden run still plays — byte-compatible with the real stream.

## Must not

- Must not fabricate rows under any failure mode.
- `run_pipeline` must not raise or leave a task stuck on "running" (D7 crash net → honest `failed` result).
- Must not break `?mock=1` or the `g` replay.
- No secrets in code, logs, or the diff — the TokenRouter key lives only in `backend/.env`.

## Evidence

- Live run `req_cdbe2260` (16s, zero console errors) + CP1 browser run `req_676fb800` over real WS with CORS preflight 200s — `completed/phase-2-status.md`.
- 29/29 pytest green at phase-2 close, mock mode, no keys — re-runnable (see Validation; the suite has grown since).
- **Back-propagation proof — four bugs only live traffic could surface**, each folded back into the adapters and `docs/VERIFY.md` so no one re-learns them:
  1. Kimi K3 rejects `temperature` ≠ 1 → HTTP 400. Param removed.
  2. MiniMax M3 prepends an un-fenced `<think>…</think>` block → JSON parse silently fell back to mock. Now stripped.
  3. 30s timeout → `ReadTimeout` on ~40% of reasoning-model planner calls, surfacing as a bogus "could you rephrase?". Raised to 75s + transport retry.
  4. Synthesizer told about undispatched subtasks reported false failures. Now only dispatched subtasks are passed (`backend/pipeline.py`, step f) — issue-04 makes the trim a no-op.
- Bugs 2 and 3 were caught only because both adapters log live-call failures instead of swallowing them.

## Validation

```
cd backend && .venv/bin/python -m pytest tests/ -q     # 29 passed at phase-2 close; suite has grown since (36+ today) — expect the current count
cd frontend && npx vite build                          # passes (verified)
# demo path:
cd backend && OTTO_MOCK=1 .venv/bin/uvicorn main:app --port 8000
cd frontend && npm run dev
open "http://localhost:5173/?mock=0&api=http://localhost:8000"
```

## Done when

- [x] All acceptance criteria observed (live run + browser + suite).
- [x] Positive AND negative paths tested: clarification, off-allowlist gate, all-failed honesty, crash net (`test_unexpected_crash_yields_honest_failed_result`).
- [x] Issue, code, tests, and docs agree (`CONTRACTS.md` field names, `VERIFY.md` gotchas recorded).
- [x] No secrets in diff or logs; key only in `.env` (gitignored).
- [x] Full suite passed (29/29 at close; suite has grown since); build passes.
- [x] Exact demo flow works manually, including the `g` safety net.
- [x] Recorded in `completed/phase-2-status.md`; Saturday PR links here for checkup.
