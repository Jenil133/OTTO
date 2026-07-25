# Flip the Retriever live and empirically score the allowlist

**Route:** pdd-change · **Phase:** 2-B completion · **Owner:** Person 3 · **Status: OPEN**

## Goal

Real browser agents run against real sites: the Retriever adapter goes live, the 8 allowlist candidates get empirically scored, and the winning phrasings land in `docs/ALLOWLIST.md`.

Where: `backend/adapters/retriever.py` — the live submit→poll path is already written with every assumption flagged `# VERIFY:` (base URL, submit/poll routes, auth header shape, session-id / progress-line / screenshot field names, terminal status strings). This issue replaces those flagged guesses with confirmed values (env overrides: `RETRIEVER_BASE_URL`, `RETRIEVER_SUBMIT_PATH`, `RETRIEVER_POLL_PATH`) and records them in `docs/VERIFY.md`. Then platform work: score every candidate row in `docs/ALLOWLIST.md`.

## Acceptance criteria

- **Given** `RETRIEVER_API_KEY` set and `OTTO_MOCK` unset, **when** a subtask targets a confirmed site, **then** a real browser session runs, live progress lines stream as §1 `agent_update` events (via the `on_step` callback), and the returned `AgentResult` validates against CONTRACTS.md §3.
- **Given** each of the 8 candidates in `docs/ALLOWLIST.md` (3 confirmed + figma.com/careers, notion.so/careers, news.ycombinator.com, bestbuy.com, newegg.com), **when** scored live on login-free / bot-defense / layout-stable / fast, **then** the table's `viewport notes` and `winning phrasing` columns are filled and losing rows are cut from the file.
- **Given** a live session exceeding the 60s hard cap, **when** the cap fires, **then** the result is a **well-formed** `partial` (if any data was collected) or `failed`, `steps_log` ends with the timeout note, and nothing raises — observable as a red pane + honest `partial` result in the UI.
- **Given** an HTTP error, garbage JSON, or a missing session id from the live API, **when** the adapter handles it, **then** the result is still a well-formed §3 `failed` with the error string in `steps_log`.
- **Given** `OTTO_MOCK=1` with the key present, **when** the suite runs, **then** mock mode still wins (`test_otto_mock_forces_mock_even_with_key`) — the keyless demo path survives.

## Must not

- Must not drive any target that is not on `docs/ALLOWLIST.md` — the pydantic Zone-1 gate (`schemas.PlanSubtask.on_allowlist`) stays intact; never weaken it to make a flaky site pass.
- Must not perform write actions on any site — read-only, Zone 1 only.
- Must not fabricate rows when extraction fails or times out.
- Must not leave a `# VERIFY:` guess in force silently — every one gets a confirmed value in `docs/VERIFY.md` or an explicit `unknown — fallback chosen`.
- Must not commit `RETRIEVER_API_KEY` (or any key) to the repo, an issue, or a log.

## Evidence

- `backend/adapters/retriever.py`: live path (submit→poll, 2s cadence, `HARD_CAP_S = 60.0`, `_timeout_result`) built and unit-covered in mock; `# VERIFY:` markers list exactly what this issue must confirm.
- `docs/ALLOWLIST.md`: the 8-row table with empty `viewport notes` / `winning phrasing` columns waiting for this scoring pass.
- `completed/phase-2-status.md` "Pending": "run Retriever against the 8 allowlist candidates, score login-free/bot-defense/layout-stable/fast, cut losers".
- Timeout/failure shaping already tested in mock: `backend/tests/test_retriever.py` (result always validates as `AgentResult`).

## Validation

```
cd backend && .venv/bin/python -m pytest tests/ -q     # suite stays green in mock mode
# live spot-check per confirmed site (key in backend/.env, OTTO_MOCK unset):
cd backend && .venv/bin/uvicorn main:app --port 8000
# POST /task targeting each confirmed site → watch agent_update lines in the UI
open "http://localhost:5173/?mock=0&api=http://localhost:8000"
# negative check: pick one slow candidate → confirm the 60s cap produces a
# partial/failed pane, not a hang.
```

## Done when

- [ ] One clean live run per confirmed site observed in the UI.
- [ ] Positive AND negative paths verified live: clean extraction, 60s cap, API error — all well-formed.
- [ ] Issue, code, `docs/ALLOWLIST.md`, and `docs/VERIFY.md` agree (no stale `# VERIFY:` guesses).
- [ ] No key material in diff or logs.
- [ ] Full suite passes in mock mode (keyless demo path intact).
- [ ] Demo flow works on the winning sites with the published phrasings.
- [ ] Linked PR passes checkup against this issue.
