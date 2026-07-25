# Phase 4 — Memory, Telemetry & Stretch Modules (to Feature Freeze)

## Goal
Attach the modules that win prizes and Q&A: **mem0 memory as a visible product surface** (powers demo Beat 2), **Respan cost/latency on stage** ("that answer cost $0.11"), the **RocketRide pipeline port** if green-lit at hour zero, and **Standing Watch** if time allows. Simultaneously harden the demo: error paths, dead-air narration, and the cached golden run. Everything here is independently droppable; the phase ends at a hard freeze.

## Window & Gate
Sat 15:00–18:00. **Gate: 18:00 FEATURE FREEZE — no new features after, under any circumstances.**

## Scope
- **In scope:** mem0 read/write + live memory panel, second-run memory flow, Respan telemetry meter, RocketRide port (conditional), Standing Watch (stretch), error paths, cached fallback run, UI polish vs mockups.
- **Out of scope:** Gmail Zone-2 connector (only if someone has done Google OAuth before AND everything above is stable — treat as bonus, not plan), EdgeOne mirror (first thing on the cut list), anything in §14 anti-scope.

## Prerequisites & Dependencies
CP2 passed (voice loop deployed). VERIFY.md: mem0 hosted decision, RocketRide GO/NO-GO, Respan provider coverage.

## Tech, Tools & Components
mem0 (hosted per VERIFY) · Respan telemetry API/headers · RocketRide runtime + pipeline JSON · Render cron or interval loop (watch).

## Parallel Track Map

| Person | Tasks |
|---|---|
| Person 1 | E |
| Person 2 | B → C (if GO) |
| Person 3 | D |
| Person 4 | A → F |

---

## Task Breakdown

### Task A — mem0 memory loop + live panel — **Person 4** — `[CODING + PLATFORM WORK]` — ~2h
- [ ] mem0 client (hosted setup on their platform per VERIFY); `user_id: "demo_user"`.
- [ ] **Read before planning:** semantic search on the utterance → inject hits into the planner input and the plan's `memory_applied` field.
- [ ] **Write after synthesis:** durable preferences only, not transient facts — bundle the extraction into the synthesizer prompt (one fewer call); write async, off the critical path; emit `memory_update` events.
- [ ] Wire the UI memory panel: list entries with source + delete button → mem0 delete API (**live-editable memory is the trust beat — deleting one on stage changes Otto's next answer**).
- [ ] Test the Beat 2 flow twice: request 1 stores "new-grad, Bay Area" → request 2 ("now check Figma and Notion") applies them unprompted and Otto SAYS so ("sticking to Bay Area new-grad roles, like before").

### Task B — Respan telemetry meter — **Person 2** — `[CODING ONLY]` — ~1h
- [ ] Pull per-request cost, latency, per-model breakdown from Respan for calls routed through the gateway.
- [ ] Emit `telemetry` events → top-bar chip (`$0.11 · 48s · 3 agents · respan`) + budget bar (`48s / 90s`) go live.
- [ ] Providers not routed through Respan: estimate locally and label honestly; never fake a sponsor number.

### Task C — RocketRide pipeline port — **Person 2** — `[CODING ONLY]` — ~1.5h — **CONDITIONAL: only if hour-zero GO**
- [ ] Define plan → dispatch → synthesize as one pipeline JSON: model steps' base URL = Respan gateway; dispatch step = external tool/custom function calling the Retriever adapter.
- [ ] Keep the plain-code orchestrator behind a flag — instant rollback if the port misbehaves.
- [ ] Run the same pipeline file locally and on Render (local/cloud parity is their pitch — prove it once).
- [ ] The voice edge stays OUTSIDE the pipeline (latency-critical, per spec placement rule).
- [ ] **If NO-GO:** skip entirely; this time flows to Task D or E. Do not retrofit an orchestration runtime at 5PM.

### Task D — Standing Watch — **Person 3** — `[CODING + PLATFORM WORK]` — ~2h — **STRETCH (high wow-per-hour, still droppable)**
- [ ] `POST /watch` stores `{url, condition, contact_mode}`; interval loop or Render cron runs a single Retriever check + one small model call to compare against the condition.
- [ ] On trigger: simplest stage version — the agent proactively **speaks** in the open session; ElevenLabs outbound call only if trivially available.
- [ ] **"Simulate trigger" button in the UI — the demo NEVER waits for a real change on stage.**
- [ ] Wire the Watches screen minimally (one card: watching → triggered states).
- [ ] If RocketRide was NO-GO in Task C: implement this watch AS a small RocketRide pipeline (fetch → compare → notify) — the honest fallback integration.

### Task E — Demo hardening + cached golden run — **Person 1** — `[CODING ONLY]` — ~2h
- [ ] Error paths verified in UI: malformed plan → Otto asks a clarifying question aloud; all agents fail → honest spoken failure + Band feed shows the attempts; one fails → partial answer that says so.
- [ ] **Cached golden run:** record the event stream of one real successful run to JSON; bind a hotkey that replays it through the UI (extends the Phase 1 mock engine). This is the on-stage safety net.
- [ ] Dead-air polish: verify Otto narrates when agents run long ("two agents are still reading — one moment").
- [ ] UI pass against the mockups: spacing, dots, mono telemetry, orb states. No new components — polish only.

### Task F — Demo script + Q&A crib sheet — **Person 4** — `[NO-CODE / PREP]` — ~0.5h
- [ ] Write the three-beat script verbatim (Beat 1 fan-out · Beat 2 memory · Beat 3 watch-if-built), including the exact spoken requests and the "hands off the keyboard" moment.
- [ ] One-page Q&A ammo from §11: dispatcher-vs-copilot line, three-zone answer for LinkedIn/email, MCP + Nexla scale answer, safety answer (read-only, allowlist, scoped OAuth, Band audit, deletable memory), business model line.

---

## Deliverables / Definition of Done
Beat 2 works end-to-end twice in a row · telemetry chip shows real numbers · RocketRide either demonstrably runs the brain or is cleanly absent · watch triggers via simulate button (if built) · golden-run hotkey works · script + crib sheet printed/onscreen. **Freeze at 18:00.**

## Acceptance Criteria / How to Verify
Run the full three-beat demo script once, on the deployed build, before 18:00. Delete a memory entry live and confirm the next answer changes. Pull the network mid-run once and confirm the UI fails gracefully + hotkey replay saves it.

## Risks & Mitigations
1. **Memory beat flaky (wrong recall / over-recall).** → Constrain writes to durable prefs only; pre-seed 2–3 known-good memories for the demo account as backup.
2. **RocketRide port destabilizes the working spine.** → Flag-gated rollback; commit/abandon decision by 16:30, never later.
3. **Time pressure squeezes hardening.** → Task E outranks C and D — cut per the global order; hardening is never the thing cut.

## Estimated Effort
P1 ≈ 2h · P2 ≈ 2.5h · P3 ≈ 2h (0 if watch is cut) · P4 ≈ 2.5h.

## Handoff to Next Phase
A frozen, deployed, three-beat-capable build with a rehearsal script, a replay hotkey, and Q&A answers. Phase 5 touches no features — only rehearsal, recording, and delivery.
