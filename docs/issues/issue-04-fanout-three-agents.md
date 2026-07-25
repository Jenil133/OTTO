# Fan out all plan subtasks to parallel agents

**Route:** pdd-change · **Phase:** 3-A · **Owner:** Person 2 · **Status: OPEN**

## Goal

`run_pipeline` dispatches **every** plan subtask concurrently (`asyncio.gather`, one `RetrieverAdapter.run_subtask` per subtask) so all three panes visibly work in parallel and the synthesizer receives one result per dispatched subtask.

Where: `backend/pipeline.py`, step e — currently `subtask = plan.subtasks[0]` ("Phase 2 scope: exactly ONE agent runs"). The UI needs no change: `frontend/src/store.js` already builds one pane per `plan.subtasks[]` entry and routes `agent_update` by `subtask_id`.

## Acceptance criteria

- **Given** a 3-subtask plan, **when** the run executes, **then** `WS /events` carries three interleaved `agent_update` streams (CONTRACTS.md §1, distinct `subtask_id`s `st_1/st_2/st_3`), all three panes animate concurrently in Ask-live, and the `result` event arrives ≤90s.
- **Given** one subtask hits the per-subtask 60s hard cap (`RetrieverAdapter.hard_cap_s`), **when** the others finish, **then** that agent's `AgentResult` (§3) is `partial`/`failed`, its final `agent_update` has `status: "failed"`, the run proceeds to synthesis **without waiting past the cap**, and the `result` is `status: "partial"` with `spoken` saying so.
- **Given** every dispatched subtask, **when** synthesis runs, **then** `MinimaxAdapter.synthesize` receives one `AgentResult` per subtask and the `dispatched_plan` trim in step f becomes a no-op (the code comment already promises this).
- **Given** a 1-subtask plan, **when** run, **then** the single-agent path still works end to end (regression).
- **Given** the run, **when** `telemetry` events tick, **then** `agents` equals the number of dispatched subtasks.
- **Given** `cd backend && .venv/bin/python -m pytest tests/ -q`, **then** every existing test still passes (36+ baseline incl. the must-not suite) plus new fan-out tests (concurrent interleave; partial-on-cap).

## Must not

- Must not block on the slowest agent beyond its 60s cap — partials flow to synthesis.
- Must not fabricate rows for a failed/timed-out pane.
- Must not break `?mock=1` or the `g` golden replay (they bypass the backend entirely — verify anyway).
- Must not change any CONTRACTS.md §1 field name or add event types — contracts are frozen.
- Must not serialize the dispatch (a `for` loop of awaits is a fail: panes must interleave).
- If the Retriever concurrency limit (VERIFY.md, Person 3) is 2, run 2 — never queue a third behind the cap and blow the budget.

## Evidence

Baseline pointers for the change:

- `backend/pipeline.py` step e: single dispatch + per-subtask `on_step` closure and final `agent_update`/`agent_screenshot` emission to generalize per subtask (`ag01` Band actor → `ag01/ag02/ag03`, map already in `_ROOM_ACTOR`).
- `backend/adapters/retriever.py`: `run_subtask` is already per-call safe (never raises, own 60s cap, `partial`-on-timeout) — mock mode paces 6 steps at `mock_step_delay`, so concurrency is visible even keyless.
- `backend/tests/test_pipeline.py`: event-sequence tests to extend (`test_happy_path_event_sequence` asserts the single-agent ordering).
- Mock planner's default plan is the 3-subtask golden plan (`test_default_plan_matches_golden_run`) — the mock demo path exercises fan-out for free.

## Validation

```
cd backend && .venv/bin/python -m pytest tests/ -q     # full existing baseline (36+ incl. must-not suite) + new fan-out tests green
cd frontend && npx vite build
# demo path (keyless):
cd backend && OTTO_MOCK=1 .venv/bin/uvicorn main:app --port 8000
cd frontend && npm run dev
open "http://localhost:5173/?mock=0&api=http://localhost:8000"
# type: "Find new-grad SDE roles at Stripe, Anthropic, Databricks"
# → 3 panes animate concurrently → one merged results card
```

## Done when

- [ ] All acceptance criteria observed over the real WS in the browser.
- [ ] Positive AND negative paths tested: 3-agent happy path, one-agent-capped → partial result, 1-subtask regression.
- [ ] Issue, code, tests, and CONTRACTS.md agree (no shape drift; step-f comment updated to reflect the no-op).
- [ ] No secrets in diff or logs.
- [ ] Full suite + `vite build` pass.
- [ ] Exact demo flow above works manually, and `?mock=1` + `g` still play.
- [ ] Linked PR passes checkup against this issue.
