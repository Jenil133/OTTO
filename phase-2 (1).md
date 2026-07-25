# Phase 2 — Text Spine End-to-End (Voice Deferred)

## Goal
A typed request travels the whole pipeline for real: **typed text → Kimi K3 plan → ONE live Retriever agent on a real site → MiniMax synthesis → answer + events rendering in the UI.** Voice is deliberately deferred so the loop is testable all morning. This is the day's load-bearing milestone — everything after it is attachment of modules.

## Window & Gate
Sat 9:45–13:00. **Checkpoint 1 @ 12:30–13:00 (over lunch):** spine works end-to-end, or the team simplifies immediately (drop to a fixed demo task). **Never proceed on a broken spine.**

## Scope
- **In scope:** planner call (JSON mode), single-agent Retriever adapter, synthesizer call, orchestrator v1, real WebSocket into the UI, typed input box, Band room + feed, empirical site testing → allowlist, deploy of the spine.
- **Out of scope:** parallel fan-out (Ph3), voice (Ph3), mem0 (Ph4 — a stub returns `[]`), Respan telemetry UI (Ph4), RocketRide port (Ph4).

## Prerequisites & Dependencies
Phase 1 gate passed: contracts frozen, VERIFY.md filled, keys in env, skeleton deployed.

## Tech, Tools & Components
TokenRouter (Kimi K3, JSON mode, context caching) · Respan gateway (route Kimi/MiniMax through it **if** VERIFY confirmed support; else direct + keep Respan for what it covers — partial use is fine) · Retriever AI API · MiniMax M3 · Band SDK/raw API · pydantic for plan validation.

## Parallel Track Map

| Person | Tasks |
|---|---|
| Person 1 | E (after finishing Ph1 A–C) |
| Person 2 | A → C → D (sequential, same owner) |
| Person 3 | B (biggest single task of the morning) |
| Person 4 | F → G |

---

## Task Breakdown

### Task A — Planner: Kimi K3 via TokenRouter — **Person 2** — `[CODING ONLY]` — ~1.5h
- [ ] Client hitting Respan's gateway URL (or TokenRouter direct per VERIFY) with the K3 model string; enable JSON mode / structured outputs; set context-caching flag on the static system prompt (name-checkable sponsor feature).
- [ ] System prompt encodes the rules: max 3 subtasks · every `target_url` from `ALLOWLIST.md` · read-only actions only (search/navigate/extract — never purchase, submit personal data, or log in) · each subtask gets explicit `success_criteria` + `output_schema` · emit `clarification_needed` instead of guessing.
- [ ] Validate output against the Plan schema (pydantic). Malformed → return a clarifying-question object, **never crash**.
- [ ] Unit-test with 3 canned utterances (jobs / shopping / ambiguous).

### Task B — Retriever adapter + empirical site allowlist — **Person 3** — `[CODING + PLATFORM WORK]` — ~2.5–3h
- [ ] Implement adapter per VERIFY: submit (target_url, natural-language instruction, expected JSON shape, hard 60s timeout) → poll or webhook → collect `{status, data, screenshot_ref, steps_log, elapsed_s}`. Timeout/failed still returns a well-formed `partial|failed` result.
- [ ] Mock mode returns a canned Stripe-jobs result (so P2 never waits on you).
- [ ] **Empirical testing (this is platform work on live sites):** run Retriever against 8–10 candidates — Stripe/Anthropic/Databricks/Figma/Notion careers, HN "Who's Hiring", 1–2 shopping/travel backups. Score: login-free? bot-defense? layout-stable? fast?
- [ ] Publish `docs/ALLOWLIST.md` with the 4–5 winners + the exact instruction phrasing that worked per site. Recommend primary demo flavor (jobs vs shopping) to the team.

### Task C — Synthesizer: MiniMax M3 — **Person 2** — `[CODING ONLY]` — ~1h
- [ ] One call merging all subtask results (including partial/failed) → `{spoken: ≤3 sentences, card: {rows, sources, flags}}`.
- [ ] Prompt handles the honesty paths: all failed → honest spoken failure; one failed → proceed on partials and say so.
- [ ] Stub the screenshot-recovery branch: if `data` empty but `screenshot_ref` exists, pass the image to M3 (multimodal) to extract. Flag as tested/untested in code comments.

### Task D — Orchestrator v1 + real event stream — **Person 2** — `[CODING ONLY]` — ~1h
- [ ] `POST /task`: mem0-stub read (`[]`) → plan → run **one** subtask via Retriever adapter → synthesize → store result in memory → respond.
- [ ] Emit WS events at every stage (`plan`, `agent_update`, `result`, plus `band_msg` via Person 4's hook) exactly per CONTRACTS.md.
- [ ] `GET /status/:id` returns current run state.

### Task E — UI: swap mock for real WebSocket + typed input — **Person 1** — `[CODING ONLY]` — ~1.5h
- [ ] Connect to `WS /events`; route incoming events into the same state object the mock fed — if Phase 1 was done right this is a thin adapter, not a rewrite.
- [ ] Add a typed input box in the transcript column (voice replaces it in Phase 3; the box stays forever as the demo fallback).
- [ ] Keep `?mock=1` fully working — it is the demo-night safety net.
- [ ] Render real plan/agent/result payloads; unknown event types log, never crash the UI.

### Task F — Band room + coordination feed — **Person 4** — `[CODING + PLATFORM WORK]` — ~2h
- [ ] Create room `otto-ops`; register persistent participants: planner, webagent-1/2/3, synthesizer (identity + audit = the prize-depth story).
- [ ] Backend hook: every lifecycle event (plan created, task assigned, agent progress, result posted, synthesis complete) posts a room message AND mirrors as a `band_msg` WS event.
- [ ] **Fallback per spec:** if the SDK fights you >45 min, build the feed as an internal event list and mirror to Band via raw API; worst case internal feed alone keeps the demo alive.

### Task G — Deploy the spine — **Person 4** — `[PLATFORM WORK ONLY]` — ~0.5h
- [ ] Push current build to Render; run one full typed request against the **deployed** URL.
- [ ] Confirm WS events reach the deployed frontend (Render WS support sanity check now, not at 7PM).

---

## Deliverables / Definition of Done
Typed request produces: validated plan → one real agent run on an allowlisted site → spoken-style text answer + results card in the UI, with plan/agent/result/band events visibly flowing. `ALLOWLIST.md` published. Spine deployed.

## Acceptance Criteria / How to Verify
**Checkpoint 1 script:** type "find new-grad SDE roles at Stripe" → within ~90s the UI shows the plan, one pane progressing, a results card, and Band lines. Run it twice (flakiness check). Kill the Retriever key → mock mode keeps the loop alive (adapter test). If CP1 fails: simplify to one hardcoded plan + one site, then move on — do not debug past 13:15.

## Risks & Mitigations
1. **Retriever flaky/blocked on targets** (top risk of the morning). → That's why allowlist selection is empirical TODAY; bad sites get cut, not fixed. Mock mode isolates it.
2. **Respan doesn't route a provider.** → Call that provider direct; keep Respan for the rest; partial use is a fine pitch.
3. **Plan JSON malformed under odd utterances.** → Validation + clarifying-question path already required in Task A; test the ambiguous case before CP1.

## Estimated Effort
P1 ≈ 1.5h · P2 ≈ 3.5h · P3 ≈ 3h · P4 ≈ 2.5h.

## Handoff to Next Phase
A working single-agent spine + allowlist + live event stream. Phase 3 only has to (a) multiply the agent count and (b) swap typed input for the ElevenLabs agent — both against interfaces that already work.
