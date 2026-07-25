# OTTO — The 7-Level Validation Ladder (PDD guide, mapped to this repo)

Every command below runs from the repo root, keyless, today. Status column is
honest: ✅ = ran green now · 🌐 = requires the live key · 🗓 = Saturday.

| L | Guide level | Otto command / artifact | Status |
|---|---|---|---|
| 1 | Static sanity | `cd frontend && npx vite build` · `cd backend && .venv/bin/python -c "import main"` | ✅ both green |
| 2 | Targeted behavior | `cd backend && .venv/bin/python -m pytest tests/test_planner.py tests/test_retriever.py tests/test_synthesizer.py -q` | ✅ per-module units |
| 3 | Negative behavior | `cd backend && .venv/bin/python -m pytest tests/test_mustnot.py -q` (7 forbidden outcomes) + negatives listed below | ✅ 7/7 |
| 4 | Integration | `cd backend && .venv/bin/python -m pytest tests/test_pipeline.py -q` · live WS browser run | ✅ · 🌐 done once |
| 5 | Regression | `cd backend && .venv/bin/python -m pytest tests/ -q` | ✅ **36 passed** |
| 6 | Manual demo | exact flow below, mock and live | ✅ mock · 🌐 live |
| 7 | Final gate | `pdd-checkup` against issue + PR | 🗓 Saturday |

## L1 — static sanity
`vite build` compiles every screen/component (✓ built, ~184 kB js). The backend
import proves FastAPI app + all 7 adapters load with **zero keys** (D6).

## L2 — targeted behavior (unit, per module)
- `tests/test_planner.py` — planner mock: jobs/shopping plans, request_id, golden-run targets, `{{ALLOWLIST}}` substitution.
- `tests/test_retriever.py` — agent steps ×6, per-site canned flavors, `on_step` callback, `OTTO_MOCK` kill-switch.
- `tests/test_synthesizer.py` — compose rules: all-ok, one-failed→partial, screenshot stub, legacy `call()`.

## L3 — negative behavior (the forbidden paths, tested by name)
New must-not suite — `tests/test_mustnot.py`, one test per "Must not" line:
`test_mustnot_plan_off_allowlist` (linkedin.com/jobs → ValidationError) ·
`test_mustnot_more_than_three_subtasks` · `test_mustnot_fabricate_rows_on_total_failure` ·
`test_mustnot_crash_on_ambiguous` · `test_mustnot_writeaction_verbs_in_planner_prompt` ·
`test_mustnot_secrets_in_tracked_files` (key-prefix scan over code/prompts/docs) ·
`test_mustnot_pipeline_die_silently`.

Pre-existing negatives (written with the features, not after):
- `test_planner.py::test_ambiguous_utterance_returns_clarification` — ask, never guess.
- `test_planner.py::test_plan_model_rejects_four_subtasks` — §2 cap in pydantic.
- `test_synthesizer.py::test_all_failed_is_honest` — no invented counts in `spoken`.
- `test_pipeline.py::test_clarification_path_partial_result_and_no_plan_event` — no agents dispatched on ambiguity.
- `test_pipeline.py::test_unexpected_crash_yields_honest_failed_result` — D7 crash net.

## L4 — integration (cross-module + persistence)
`tests/test_pipeline.py` drives the whole spine (plan → agent_update ×6 →
synth → result) over a fake `main.emit`, asserting CONTRACTS.md §1 event order,
Band-feed mirroring, and that `TASKS` ends `done|failed` with a stored result
(the `GET /status/:id` persistence surface). Live variant: real WS browser run
over TokenRouter — request `req_cdbe2260`, real planner (gemini-3.5-flash-lite)
→ mock Retriever → real MiniMax-M3 synthesis, 16 s, zero console errors. It
exposed 4 live-only bugs, all fixed in adapters (never in tests): three logged
in `docs/VERIFY.md` "Gotchas found live", the fourth (synthesizer told about
undispatched subtasks) documented at the dispatch site in `backend/pipeline.py`.

## L5 — regression (full suite)
`cd backend && .venv/bin/python -m pytest tests/ -q` → **36 passed** (29 prior
+ 7 must-not), ~2 s, keyless. Run after every generation step — tests are never
weakened to pass (must-not names make that visible in review).

## L6 — manual demo (the exact presentation flow)
1. `cd frontend && npx vite dev` → open `http://localhost:5173/?mock=1`.
2. Press run → 62 s golden replay (`frontend/src/mockRun.js`): plan card, 3
   agent panes, feed rail, telemetry ticks → results card → memory beat.
3. Hotkey `g` replays the golden run at any moment — **even under `?mock=0`**
   (demo-night safety net, byte-compatible with the real WS stream).
4. Live path: `cd backend && .venv/bin/uvicorn main:app --port 8000` (key in
   `backend/.env`), open `?mock=0&api=http://localhost:8000` → typed request
   rides the real planner/synthesizer over one WebSocket.

## L7 — final gate
`pdd-checkup` needs a GitHub issue + PR — the repo goes to GitHub **Saturday
morning** (git init + push is the first task). Until then the interim gate is
manual: every phase file in `docs/prompts/` carries "Definition of Done" +
"Acceptance Criteria / How to Verify" sections, `completed/*-status.md` records
what shipped, and `PDD.md` §5 scores all 7 DoD criteria honestly (two ⚠️s, both
"no repo yet").

## Run the whole ladder (L1–L5, one block, keyless)
```bash
cd /path/to/Otto/frontend && npx vite build && \
cd ../backend && .venv/bin/python -c "import main" && \
.venv/bin/python -m pytest tests/ -q          # 36 passed = L2+L3+L4+L5
```
