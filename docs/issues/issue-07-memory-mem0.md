# Wire the mem0 memory loop and light up the "otto knows" pills

**Route:** pdd-change · **Phase:** 4-A · **Owner:** Person 4 · **Status: OPEN**

## Goal

Otto remembers durable preferences across requests: mem0 is read before planning and written after synthesis (async, off the critical path), with "otto knows" pills and the Memory screen rendering live — demo Beat 2.

Where: `backend/adapters/mem0.py` — `read()` is a Phase-2 stub that always returns `[]` (its own docstring says Phase 4 replaces it with real semantic search; `_mock()` shows the §4 entry shape). `backend/pipeline.py` step b already calls `Mem0Adapter().read(text)` and feeds the planner; the write hook goes after step f. Frontend is done: `store.js` reduces `memory_update` into Memory-screen sections and appends preference pills to the "otto knows" rail; the `plan` reducer maps `recall` to `knows`. Hosted-vs-self-host + the add/search one-liners are the `docs/VERIFY.md` Person 4 answers. `user_id: "demo_user"`.

## Acceptance criteria

- **Given** a first request stating preferences ("new-grad roles, Bay Area only"), **when** synthesis completes, **then** §1 `memory_update` events emit (shape per CONTRACTS.md §1/§4, durable preferences only) and the Memory screen lists the new entries with their `request_id`.
- **Given** a second request that omits those preferences ("now check Figma and Notion"), **when** planned, **then** `Mem0Adapter.read` returns the stored prefs, the `plan` event's `recall` field carries them, the "otto knows" pills render from t≈1s, and the `spoken_ack` references them ("sticking to Bay Area new-grad roles, like before").
- **Given** an entry deleted in the Memory screen, **when** the delete hits the mem0 delete API, **then** the next run's `plan.recall` no longer contains it — the next answer observably changes (the on-stage trust beat).
- **Given** mem0 is slow or down, **when** the write fires, **then** it runs async off the critical path — the `result` event's timing is unaffected and the pipeline never fails because of a memory error.
- **Given** keyless mock mode, **when** the suite runs, **then** all existing tests still pass and new tests cover read-injects-recall and write-does-not-block.

## Must not

- Must not write transient facts — durable preferences only (phase-4.md Task A rule); extraction is bundled into the synthesizer prompt, not an extra LLM call.
- Must not block the critical path on any mem0 call; a memory failure must never fail a run.
- Must not expose `MEM0_API_KEY` to the frontend — deletes go through the backend.
- Must not change the `memory_update` event shape or §4 entry shape — the reducer already consumes them.
- Must not break the keyless demo path (`OTTO_MOCK=1` still runs with the stub/canned behavior).

## Evidence

- `backend/adapters/mem0.py`: the stub to replace, with the §4 mock entries as the target shape.
- `backend/pipeline.py` step b: read hook already in place (`memory: List[str] = await Mem0Adapter().read(text)`).
- `frontend/src/store.js` `memory_update` / `plan` cases + `frontend/src/screens/Memory.jsx` (sections, search, delete — built in Phase 1).
- `docs/VERIFY.md` Person 4 mem0 lines (hosted decision, add/search one-liners) — answered at the 9:45 gate.

## Validation

```
cd backend && .venv/bin/python -m pytest tests/ -q     # existing + new memory tests green
cd frontend && npx vite build
# Beat 2 manual flow — run TWICE in a row (phase-4.md Task A):
#   request 1: "find new-grad SWE roles in the Bay Area at Stripe, Anthropic, Databricks"
#     → memory_update events → entries visible on the Memory screen
#   request 2: "now check Figma and Notion"
#     → "otto knows" pills at t≈1s, spoken ack references the stored prefs
#   then: delete one entry on the Memory screen → request 3 no longer recalls it
```

## Done when

- [ ] Beat 2 works end-to-end twice in a row on the deployed build.
- [ ] Positive AND negative paths tested: recall applied, delete-changes-answer, mem0-down never blocks a run.
- [ ] Issue, code, tests, CONTRACTS.md §4, and `docs/VERIFY.md` agree.
- [ ] No secrets in diff, logs, or frontend bundle.
- [ ] Full suite + build pass.
- [ ] Exact Beat 2 demo flow (including live delete) works manually.
- [ ] Linked PR passes checkup against this issue.
