# Phase 3 — Parallel Fan-Out + Voice Layer

## Goal
Otto becomes Otto: **speak a request → Otto acks in voice → three browser agents visibly work in parallel in the viewports → Otto speaks the merged answer.** This phase delivers the entire "wow" of demo Beat 1 and contains the day's #1 integration risk (the ElevenLabs tool round-trip), which is why it gets a pair task and a pre-planned fallback ladder.

## Window & Gate
Sat 13:00–15:00. **Checkpoint 2 @ 15:00:** one full voice run works on the **deployed** build. Deploy happens in this phase, mid-afternoon — not at the end of the day.

## Scope
- **In scope:** concurrent 3-agent dispatcher, live viewports (embed or log+screenshot fallback), ElevenLabs conversational agent + `run_task` tool + widget/SDK embed, mid-afternoon deploy, mic/hotspot logistics, pitch skeleton.
- **Out of scope:** mem0 (Ph4), Respan meter (Ph4), RocketRide (Ph4), Standing Watch (Ph4).

## Prerequisites & Dependencies
CP1 passed (working single-agent text spine). VERIFY.md answers for: ElevenLabs tool mechanism + timeout ceiling + embed path; Retriever concurrency limit + live-view embeddability.

## Tech, Tools & Components
ElevenLabs conversational-agents platform (NOT raw TTS — the depth play) · asyncio.gather fan-out · Retriever concurrent sessions · Render.

## Parallel Track Map

| Person | Tasks |
|---|---|
| Person 1 | B (pair) → helps C if done early |
| Person 2 | A → B (pair) |
| Person 3 | C |
| Person 4 | D |

---

## Task Breakdown

### Task A — Parallel dispatcher (the fleet) — **Person 2** — `[CODING ONLY]` — ~1h
- [ ] Fan the plan's subtasks out with `asyncio.gather` — one Retriever session per subtask, respecting the concurrency limit from VERIFY (if limit is 2, the demo runs 2 — two still reads as a fleet).
- [ ] Per-subtask hard 60s timeout; the run **never blocks on the slowest agent** — partials flow to synthesis.
- [ ] Emit `agent_update` events per step per agent (pane ids `webagent-1/2/3`); emit results to synthesizer as they complete.
- [ ] Test: 3-subtask plan against 3 allowlisted sites → 3 panes animate concurrently, answer arrives ≤90s.

### Task B — ElevenLabs conversational agent + embed — **Person 1 + Person 2** — `[PAIR TASK · CODING + PLATFORM WORK]` — ~2h (the day's #1 risk)
- [ ] **Platform:** in the ElevenLabs console create the Otto agent — personality prompt ("You are Otto… acknowledge immediately, confirm task understanding in one sentence, never fabricate results, narrate progress if the tool is slow"), pick a voice, register tool `run_task(task_description)` → `POST /task` on Render.
- [ ] **Timeout strategy (decided by VERIFY, in order of preference):** (1) tool call waits 60–90s → simplest, use it; (2) ceiling too low → two-tool pattern: `dispatch_task` returns immediately + `check_result` polling tool; (3) or backend-initiated contextual update / client-SDK message injection when the result lands. Implement exactly one; stub none.
- [ ] **Coding:** embed the widget or React SDK in the transcript column; wire the on-screen orb to push-to-talk (no open mic, ever); mirror agent speech into transcript bubbles.
- [ ] Dead-air behavior: agent verbally acks ("On it — checking three sites") and narrates if slow.
- [ ] **Timebox 90 min of pairing.** If still broken: fall back to typed input + voice **output** (backend sends answer text to TTS) — the soul survives; revisit only if Phase 4 goes smoothly.

### Task C — Live viewports — **Person 3** — `[CODING ONLY]` — ~1.5–2h
- [ ] If VERIFY said Retriever live view is embeddable: iframe/embed each session into its `<AgentPane>`.
- [ ] Else (the likely path): stream `steps_log` lines into the pane + render `agent_screenshot` events as periodic stills — panes must visibly "work", security-camera style.
- [ ] Progress bar + `step x/6` from step counts; status dot transitions idle→working→done/failed; elapsed timer.
- [ ] Failure is a feature: a failed pane goes red with its last step visible — "even failure looks alive."

### Task D — Mid-afternoon deploy + stage logistics + pitch skeleton — **Person 4** — `[PLATFORM WORK ONLY / NO-CODE]` — ~1.5h
- [ ] Deploy the full current build to Render **now** (deploy problems found at 3PM are a chore; at 7PM they're fatal). Verify the ElevenLabs tool URL points at the deployed backend.
- [ ] Physical setup in the actual demo corner: phone hotspot (never venue WiFi), hardwired/lapel push-to-talk mic, one full run on this exact setup.
- [ ] Draft the pitch skeleton: 30-sec opener + 2-min structure (cold-open live Beat 1 → one architecture slide with the three-zone + fleet story, sponsors named in place → memory beat → cost line + "every request is this one JSON" → "Every assistant can talk. Otto has hands." → ask).

---

## Deliverables / Definition of Done
On the deployed build, over hotspot: press-to-talk a jobs request → verbal ack ≤2s → 2–3 panes work in parallel → Otto speaks a ≤3-sentence comparison → results card renders. Band feed scrolling throughout.

## Acceptance Criteria / How to Verify
**Checkpoint 2 script:** one full voice run, deployed, on the demo-corner setup. Also verify the failure paths once: kill one agent mid-run → synthesis proceeds on partials and says so.

## Risks & Mitigations
1. **ElevenLabs tool round-trip exceeds ceiling.** → Fallback ladder pre-planned in Task B; final rung (typed input + voice out) is always available and pre-built from Phase 2.
2. **Concurrency limit < 3 on hackathon credits.** → Run 2 agents; the fan-out visual survives; say "fleet" anyway.
3. **Deployed WS/latency differs from local.** → That is exactly why deploy is at 3PM; CP2 runs on the deployed URL only.

## Estimated Effort
P1 ≈ 2h · P2 ≈ 2.5h (some overflow into early Ph4 acceptable) · P3 ≈ 2h · P4 ≈ 1.5h.

## Handoff to Next Phase
The full demo Beat 1 exists. Phase 4 attaches the differentiator modules (memory = Beat 2, telemetry = the investor line, watch = Beat 3) onto a loop that already works — each independently droppable per the cut order.
