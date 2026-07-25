# Build Standing Watch with a simulate-trigger button

**Route:** pdd-change · **Phase:** 4-D (stretch — droppable per the cut order) · **Owner:** Person 3 · **Status: OPEN**

## Goal

`POST /watch` becomes a living loop — a periodic single-agent check that compares a page against a condition and makes Otto proactively speak on trigger — with a **simulate-trigger button** so the demo never waits for reality on stage.

Where: `backend/main.py` — `POST /watch` already stores `{url, condition, contact_mode}` in `WATCHES` and returns `{watch_id, status: "watching"}` per CONTRACTS.md §6; its docstring says "the check loop is Phase 4-D". Add an interval loop (or Render cron) running one `RetrieverAdapter.run_subtask` check + one small model call comparing the extract to `condition`. Frontend: `frontend/src/screens/Watches.jsx` is a static screen rendering `state.watches` with statuses `watching | triggered | paused` — wire one card live and add the simulate button.

## Acceptance criteria

- **Given** `POST /watch {url, condition, contact_mode}`, **when** accepted, **then** the §6 response shape is unchanged AND a periodic check loop is scheduled for that watch (observable in backend logs: one check cycle = one Retriever call + one compare call).
- **Given** the simulate-trigger button on the Watches screen, **when** clicked, **then** the watch card flips `watching → triggered` and Otto proactively speaks the notification in the open session — no real page change required.
- **Given** a real condition match on a checked URL, **when** the loop's compare call says triggered, **then** the exact same trigger path fires as the simulate button (one code path, two entry points).
- **Given** a check that fails (site error, timeout, malformed extract), **when** the cycle ends, **then** the watch stays `watching`, the loop continues on schedule, and nothing crashes — same never-raise discipline as the pipeline (D7).

## Must not

- Must not let the demo depend on a real change — the simulate button is a hard requirement, not a nicety (phase-4.md Task D: "the demo NEVER waits for a real change on stage").
- Must not watch a target off `docs/ALLOWLIST.md` with a browser agent — the Zone-1 gate applies to watch checks too.
- Must not run checks on the request path or block `POST /task` / `WS /events` — the loop is background-only.
- Must not change the §6 `POST /watch` response shape.
- Must not attempt ElevenLabs outbound calling unless it is trivially available — the open-session spoken trigger is the stage version.

## Evidence

- `backend/main.py`: `WATCHES` store + `create_watch` endpoint (shape already live, loop absent by design).
- `frontend/src/screens/Watches.jsx`: card UI with `watching`/`triggered`/`paused` states, built in Phase 1 as a bonus.
- `phase-4.md` Task D: scope, the RocketRide-fallback note (if RocketRide was NO-GO, implement this watch AS a small fetch → compare → notify pipeline), and the stretch/droppable status.

## Validation

```
cd backend && .venv/bin/python -m pytest tests/ -q     # existing + new watch tests green
cd frontend && npx vite build
# demo path (Beat 3):
cd backend && OTTO_MOCK=1 .venv/bin/uvicorn main:app --port 8000
# register: POST /watch {"url":"stripe.com/jobs","condition":"a new new-grad role appears","contact_mode":"speak"}
# → Watches screen shows the card "watching"
# → click simulate-trigger → card flips to "triggered", Otto speaks
# negative check: point a watch at a failing check → card stays "watching", loop survives
```

## Done when

- [ ] Simulate-trigger flow works on the deployed build (Beat 3, if kept past the cut line).
- [ ] Positive AND negative paths tested: simulated trigger, real-compare trigger path, failing check keeps watching.
- [ ] Issue, code, tests, and CONTRACTS.md §6 agree.
- [ ] No secrets in diff or logs.
- [ ] Full suite + build pass; nothing on the main spine regressed.
- [ ] Exact Beat 3 demo flow works manually via the simulate button.
- [ ] Linked PR passes checkup against this issue.
