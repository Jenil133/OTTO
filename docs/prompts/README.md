# Prompt Provenance Manifest — the PDD inversion

**Prompt files are source; code is generated output.**

The files in this directory were the **literal inputs** fed to coding agents
(Claude Code multi-agent workflows). The frontend, backend, and test suite in
this repo are their **output**. Nothing here is documentation written after
the fact — it is the build's source, committed so a judge can diff claim
against code.

## Build-prompt pack (this directory) — what each file generated

| Prompt file | Generated | Verify it yourself |
|---|---|---|
| `README-master-plan.md` | The plan-of-plans: scope, phase gates, prompt inventory, person-hour budget. Governs every file below. | Cross-check any claim in it against the repo — that is the point. |
| `architecture-diagrams.md` | The D1–D10 decisions the generated code cites by name in its docstrings (D6 mock/live, D7 never-raise, D10 watch loop…). | `grep -rn "D7" backend/` — the generated code references its source decisions dozens of times. |
| `phase-1.md` | Entire frontend UI shell: `frontend/src/screens/` (AskIdle, AskLive, Results, Memory, Watches, Connect), components, `mockRun.js` golden run, `tokens.css`, store, events. Plus repo/docs skeleton and the VERIFY checklist discipline. | `cd frontend && npx vite build` (passes). Golden replay: `?mock=1` + hotkey `g`, byte-compatible with the real WS stream. |
| `phase-2.md` | Entire backend text spine: `backend/main.py`, `pipeline.py`, `schemas.py` (pydantic allowlist gate), `adapters/` (kimi, minimax, retriever, base), the runtime prompts `backend/prompts/planner.md` + `synthesizer.md`, and `backend/tests/`. | `cd backend && .venv/bin/python -m pytest tests/ -q` → **36 passed** (incl. 7 negative-path `test_mustnot` tests). Live run documented in `completed/phase-2-status.md` (real planner + real MiniMax-M3 over TokenRouter, 16s, zero console errors). |
| `phase-3.md` | **Not yet executed** — Saturday 13:00–15:00 (fan-out ×3 + ElevenLabs voice). Its runtime-prompt slot is already staged: `backend/prompts/personality.md` (Define/Constrain frozen, TODOs marked). | Open the staged skeleton; constraints are frozen before generation — the PDD order, visible. |
| `phase-4.md` | **Not yet executed** — Saturday 15:00–18:00 (mem0, telemetry, Standing Watch). Staged slot: `backend/prompts/watch-compare.md`. | Same: Define/Constrain committed ahead of Generate. |
| `phase-5.md` | No code output **by design** — freeze, rehearsal, recorded backup, demo delivery. | Its exit criteria are the demo itself. |

Execution record (the PDD Review stage, per phase): `completed/phase-1-status.md`,
`completed/phase-2-status.md` — what shipped, what was verified live, what got
back-propagated. Lessons that only surfaced live (Kimi's temperature-400,
MiniMax's un-fenced `<think>` block, reasoning-model timeouts) were written
back into `docs/VERIFY.md` and into the adapters' comments — the
back-propagation leg of the cycle.

Copies here are the canonical committed pack; identical working originals sit
at the repo root (`diff` them — they match).

## Runtime prompts (`backend/prompts/`) — the product's own interfaces

The product is prompt-driven too: prompts are the interfaces between every
component, code is dispatch plumbing. Each file carries its own
`PDD SOURCE ARTIFACT` provenance header (consumer, output contract,
verification, back-propagation).

| File | Role | Status |
|---|---|---|
| `planner.md` | System prompt for the planner (loaded verbatim by `adapters/kimi.py`, allowlist substituted) → strict Plan/Clarification JSON, re-validated by `schemas.Plan`. | **Live-verified** |
| `synthesizer.md` | System prompt for MiniMax M3 (loaded verbatim by `adapters/minimax.py`) → strict result JSON with non-negotiable honesty paths. | **Live-verified** |
| `personality.md` | ElevenLabs conversational-agent prompt (Otto's voice edge). | Staged skeleton — Ph3-B |
| `watch-compare.md` | Standing-Watch condition check → strict `{"met", "reason"}` verdict. | Staged skeleton — Ph4-D |

Per-site agent instructions are the fifth prompt surface: composed **at
runtime by the planner itself** (`instruction` field per subtask) — a prompt
that writes prompts. Winning phrasings get promoted into `docs/ALLOWLIST.md`
(Ph2-B, Saturday).

## The rule

**Every prompt gets committed — evidence trail, not folklore.** If a prompt
steered a model — coding agent or runtime — it lives in this repo, verbatim,
with its provenance header. What you can read here is what actually ran.
