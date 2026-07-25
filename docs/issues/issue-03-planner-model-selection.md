# Select the planner model by measured benchmark, not vibes

**Route:** pdd-change · **Phase:** 2 · **Owner:** Person 3 · **Status: DONE (retroactive)**

## Goal

Pick the shipping planner model by timing real candidates through one gateway (same key, same prompt) against the D2 planning budget — swappable by one env var with zero code change.

## Acceptance criteria

- **Given** the same TokenRouter key and the same planner prompt, **when** each candidate model plans the jobs utterance, **then** the shipping model returns a valid plan in ≤10s (D2 budget: 5–10s). **Observed: gemini-3.5-flash-lite, 2.8s.**
- **Given** the jobs utterance, **when** the shipping model plans, **then** the plan has exactly **3 subtasks**, every `target` on `docs/ALLOWLIST.md` (§2 gate — `test_jobs_utterance_returns_allowlisted_plan`).
- **Given** 5 repeat runs, **when** timed, **then** 5/5 consistent. **Observed: 2.6–2.9s, identical allowlist targets.**
- **Given** an ambiguous ask, **when** the shipping model plans, **then** it still returns a Clarification — the honesty path survives the swap (`test_ambiguous_utterance_returns_clarification`).
- **Given** a model swap, **when** shipped, **then** only `PLANNER_MODEL` in `backend/.env` changes — zero code diff.

## Must not

- Must not ship a model that collapses fan-out to 1 subtask — **gpt-5.4-mini was rejected on exactly this** (breaks the 3-pane demo visual).
- Must not pick by vibes: every row below is a measured live number, never embellished.
- Must not blow the 60–90s total budget: a 28s planner (Kimi K3) fails even though its plans are correct.
- Must not paste the gateway key into issues, prompts, or commits.

## Evidence

Measured live through TokenRouter (same key, same prompt) — recorded in `docs/VERIFY.md` and `completed/phase-2-status.md`:

| model | latency | plan |
|---|---|---|
| **google/gemini-3.5-flash-lite** | **2.8s** | 3 subtasks — **shipping** |
| openai/gpt-5.4-mini | 3.9s | 1 subtask — rejected, breaks fan-out |
| x-ai/grok-4.1-fast | 7.6s | 3 subtasks |
| z-ai/glm-5-turbo | 10.4s | 3 subtasks |
| moonshotai/kimi-k3 | 28.0s | 3 subtasks (reasoning model — burns tokens the task doesn't need) |

Consistency: 5/5 runs at 2.6–2.9s, identical targets, clarify-on-ambiguous preserved.

## Validation

```
cd backend && .venv/bin/python -m pytest tests/ -q      # full suite green (29 at close, 36+ today) — planner suite covers
                                                        # allowlisted plan, ≤3-subtask cap,
                                                        # clarification path
# reproduce a benchmark row: set PLANNER_MODEL in backend/.env, restart, time a
# typed request through the demo path (issue-02 Validation) — no code change.
```

## Done when

- [x] Shipping model meets every criterion above with measured numbers.
- [x] Negative finding recorded (the 1-subtask model rejected, the 28s model rejected) — not just the winner.
- [x] Issue, code (`PLANNER_MODEL` env), tests, and `docs/VERIFY.md` agree.
- [x] No key material anywhere in the trail.
- [x] Full suite passed after the swap (29/29 at close; suite has grown since).
- [x] Live demo path runs on the shipping model (`req_cdbe2260`, issue-02).
- [x] Saturday PR links here for checkup.
