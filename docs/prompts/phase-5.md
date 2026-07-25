# Phase 5 — Freeze, Rehearse, Record, Demo

## Goal
Convert a working build into a **won demo**. No feature code exists in this phase — only rehearsal to fluency, a recorded backup, a tightened pitch, and controlled delivery of the three beats to judges, sponsors, and investors.

## Window & Gate
Sat 18:00–21:00. Rehearsal 18:00–19:30 · Demos 19:30–21:00. The 18:00 freeze from Phase 4 is absolute: **bug fixes only, zero new features.**

## Scope
- **In scope:** ≥5 full rehearsals on the deployed build over hotspot, backup video, pitch finalization, stage/AV setup, bug-fix-only patches, live demo execution.
- **Out of scope:** everything else. If someone opens an editor for a feature, another team member closes it.

## Prerequisites & Dependencies
Phase 4 freeze delivered: deployed build, three-beat script, golden-run hotkey, Q&A crib sheet, tested demo-corner setup (hotspot + hardwired mic).

## Tech, Tools & Components
The deployed Render build · phone hotspot · hardwired/lapel push-to-talk mic · screen recorder (QuickTime/OBS) · presenter laptop with the backup video pre-loaded.

## Parallel Track Map

| Person | Tasks |
|---|---|
| All four | A (rotating roles) |
| Person 1 | D |
| Person 2 | E |
| Person 3 | B |
| Person 4 | C → presents |

---

## Task Breakdown

### Task A — Rehearse ×5 on the deployed build — **All 4** — `[NO-CODE / PREP]` — 18:00–19:30 core activity
- [ ] Full three-beat script, every time, on the exact stage setup: hotspot, hardwired mic, deployed URL, pre-warmed allowlisted sites.
- [ ] Roles each run: **Presenter** (Person 4, the best speaker) · **Operator** (drives UI, owns the golden-run hotkey) · **Timer** (2-min discipline) · **Observer** (notes every stumble).
- [ ] Discipline per spec: exactly ONE full live run per beat; push-to-talk only; hands demonstratively off the keyboard during Beat 1.
- [ ] Drill the failure branch at least once: mid-run stall → operator hits the golden-run hotkey → presenter narrates without breaking stride.
- [ ] After each run: 3-minute fix-the-stumbles huddle; only wording and operation change, never features.

### Task B — Backup video — **Person 3** — `[NO-CODE / PREP + PLATFORM]` — ~30 min @ ~18:30
- [ ] Screen-record one clean full run (system audio + Otto's voice) at ≈6:30PM as mandated by the spec.
- [ ] Trim to demo length; load the file locally on the presenter laptop (not cloud-only); test playback on the stage display/adapter.
- [ ] This is the absolute last line of defense — after hotkey replay, before it, never instead of rehearsing.

### Task C — Pitch final + Q&A drill — **Person 4** — `[NO-CODE / PREP]` — ~1h (interleaved with A)
- [ ] Lock the 30-second opener verbatim (spec §12) and the 2-minute structure: cold-open live Beat 1 (no slides first — the fan-out IS the hook) → one architecture slide (three zones + fleet, sponsors named in place) → Beat 2 memory payoff → cost line + "every request is this one JSON" (only if RocketRide shipped — else drop that clause) → close: **"Every assistant can talk. Otto has hands."** → the ask.
- [ ] Sponsor depth map (§9) as a one-liner-per-sponsor crib — judges score depth, name features precisely (JSON mode, context caching, tool calls, audit log, gateway).
- [ ] Name the event's theme explicitly, once: "Otto IS prompt-driven development — a spoken prompt becomes a planner prompt becomes three browser-agent prompts. And we built it the same way: our phase plan was the prompt pack for our coding agents." (Prompt inventory table in README-master-plan.md.)
- [ ] Team drills Q&A: each member fires two §11 questions at the presenter; answers ≤20 seconds each.

### Task D — Bug-fix-only mode + hotkey verification — **Person 1** — `[CODING — BUGFIX ONLY]` — on-call
- [ ] Fix only what rehearsal breaks; every patch redeployed and re-verified with one full run before the next rehearsal.
- [ ] Verify the golden-run hotkey and `?mock=1` on the actual stage machine + display.
- [ ] 19:15: hands off the keyboard for good.

### Task E — Infra health + restart drill — **Person 2** — `[PLATFORM WORK ONLY]` — on-call
- [ ] Render service health, env vars intact, no free-tier idle spin-down surprise (hit the URL 5 min before demo slot).
- [ ] Write the 5-line restart procedure (backend, frontend, ElevenLabs agent re-link) on paper; drill it once.
- [ ] Hotspot battery, backup phone hotspot, mic cable spare.

### Demo delivery — 19:30–21:00
- [ ] Warm the deployed app + allowlisted sites 5 minutes before the slot.
- [ ] Beat 1: fan-out live, cost line on screen. Beat 2: memory applied unprompted + optional live delete. Beat 3 only if built and rehearsed clean.
- [ ] Close + ask. Q&A per crib sheet. Do not attempt anything unrehearsed on stage.

---

## Deliverables / Definition of Done
≥5 clean rehearsals logged · backup video local on the presenter machine · pitch memorized to time · demo delivered with all three defense layers standing (live run → hotkey replay → video).

## Acceptance Criteria / How to Verify
The final rehearsal (run 5+) executes with zero operator hesitation and lands under time. Presenter answers all six crib-sheet questions unaided.

## Risks & Mitigations
1. **Venue WiFi/AV chaos.** → Already hotspot + hardwired mic by design; rehearsed on that exact setup; spares staged.
2. **Live-run stall on stage.** → One-run-per-beat rule + hotkey replay drilled in Task A; presenter narration covers the switch.
3. **Overtime / rambling.** → Timer role in every rehearsal; the 2-minute structure is fixed; cut Beat 3 before cutting the close.

## Estimated Effort
All 4 ≈ 2–2.5h each, mostly Task A.

## Handoff
There is no next phase — there is a stage. Every assistant can talk. Otto has hands. 🚀
