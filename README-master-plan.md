# OTTO — Master Build Plan (5 Phases · 4 People · 48 Person-Hours)

**Event:** Build Fast. Launch Loud. — a **Prompt Driven Development (PDD)** hackathon — Sat July 25, 2026, 9:00AM–9:00PM, Venture Dock, Palo Alto
**Prime directive:** A narrow thing that fully works beats a broad thing that half-works. Spine first, sponsors as droppable modules.

---

## Work-Type Legend (used in every task heading)

| Tag | Meaning |
|---|---|
| `[CODING ONLY]` | Pure code in the repo. No dashboards, no accounts. |
| `[PLATFORM WORK ONLY]` | Sponsor consoles, accounts, keys, deploys, device setup. No code. |
| `[CODING + PLATFORM WORK]` | Both: configure on a sponsor dashboard AND write integration code. |
| `[NO-CODE / PREP]` | Testing, verification, rehearsal, pitch, docs, video. |
| `[PAIR TASK]` | Two people together — reserved for the riskiest integrations. |

---

## Role Map

| Person | Role | Owns |
|---|---|---|
| **Person 1** | Voice + Frontend | UI (all screens), ElevenLabs embed, demo polish |
| **Person 2** | Backend + Pipeline | FastAPI, planner (Kimi), synthesizer (MiniMax), dispatcher, Respan, RocketRide |
| **Person 3** | Web Agents + Data | Retriever integration, site allowlist, viewports, Standing Watch, backup video |
| **Person 4** | Memory + Band + Deploy + Pitch | mem0, Band room, Render deploys, demo script, pitch (best speaker) |

---

## Master Clock & Gates

| Phase | Window | Gate (sync point) |
|---|---|---|
| **Phase 1 — UI Shell + Foundations** | Tonight (UI head start) + Sat 9:00–9:45 | **9:45** — keys verified, RocketRide go/no-go, contracts frozen. UI-on-mock plays by ~11:00 latest. |
| **Phase 2 — Text Spine End-to-End** | 9:45–13:00 | **CP1 @ 12:30–13:00** — typed request → plan → 1 live agent → synthesized answer in UI. Never proceed on a broken spine. |
| **Phase 3 — Fan-Out + Voice** | 13:00–15:00 | **CP2 @ 15:00** — full voice loop works once, on the **deployed** build. |
| **Phase 4 — Memory, Telemetry, Stretch** | 15:00–18:00 | **18:00 FEATURE FREEZE** — hard stop, no exceptions. |
| **Phase 5 — Rehearse + Demo** | 18:00–21:00 | Demos 19:30–21:00. |

---

## Global Cut Order (if behind, drop in this order)

EdgeOne mirror → Standing Watch → RocketRide (unless committed & working) → 3rd parallel agent (two still reads as a fleet) → Band (internal feed survives) → voice **input** (keep voice output: type the request, Otto still speaks).

**Never cut:** the fan-out visual, the spoken answer, the memory beat.

---

## Contracts Frozen in Phase 1 (these decouple the 4 builders)

1. **WebSocket event** — `{"type": "plan|band_msg|agent_update|agent_screenshot|result|telemetry|memory_update", "payload": {...}, "ts": ...}` — the entire UI renders off this one stream.
2. **Plan JSON** (Planner → Dispatcher) — spec §5, max 3 subtasks, allowlist-only, read-only.
3. **Agent result** — `{"subtask_id", "status": "ok|partial|failed", "data", "screenshot_ref", "steps_log", "elapsed_s"}`.
4. **mem0 entry** and **Band message** shapes — spec §5.

Rule: nobody changes a contract after 9:45 without telling all four people out loud.

---

## Ground Rules

- Every external call goes through a **thin adapter with a mock mode** — the spine must run on any subset of live keys.
- **Deploy early:** current build on Render by mid-afternoon (CP2), never at 7PM.
- Stage discipline: push-to-talk hardwired mic, phone hotspot, pre-warmed allowlisted sites, one full live run per demo beat, cached golden run behind a hotkey, backup video recorded at ~6:30PM.
- **PDD evidence trail:** every prompt is a committed artifact, not something typed and lost. Runtime prompts (planner, synthesizer, Otto personality, watch-compare) live in `backend/prompts/`; build prompts given to coding agents — including these phase files and diagrams — live in `docs/prompts/`. A judge who asks "show me your PDD" gets files opened, not claims made.
- Anti-scope (§14): no Zone-3 targets, no purchases/form submissions, no accounts/auth, no DB, no wake-word, nothing new after 18:00.

---

## PDD — Theme Compliance (this IS a Prompt Driven Development hackathon)

Otto is PDD twice over — say it to judges in this order:

1. **The product is prompt-driven.** A spoken prompt → the planner prompt (Kimi K3) → three natural-language browser-agent prompts (Retriever — the sponsor's own category name is "prompt-driven web agents") → the synthesizer prompt (MiniMax). Prompts are the interfaces between every component; the code between them is just dispatch plumbing.
2. **The build is prompt-driven.** This plan — phase files + architecture-diagrams.md + CONTRACTS.md — is itself the prompt pack fed to coding agents that generate the UI and backend. A prompt-driven product, built with prompt-driven development.

**Prompt inventory (where each prompt is authored):**

| Prompt artifact | Phase · Task |
|---|---|
| Otto personality prompt (ElevenLabs conversational agent) | Ph3 · B |
| Planner system prompt (Kimi K3 — rules, allowlist, JSON schema) | Ph2 · A |
| Per-site agent instructions (winning phrasings → `ALLOWLIST.md`; composed per-request by the planner at runtime) | Ph2 · B |
| Synthesizer prompt (MiniMax — merge rules + honesty paths + screenshot recovery) | Ph2 · C |
| Memory-extraction clause (bundled inside the synthesizer prompt) | Ph4 · A |
| Watch-condition compare prompt ("condition met?") | Ph4 · D |
| Judge-facing PDD line in the pitch | Ph5 · C |

## Person-Hour Budget (Saturday, approximate)

| Person | Ph1 | Ph2 | Ph3 | Ph4 | Ph5 | Total |
|---|---|---|---|---|---|---|
| P1 | 3.0* | 1.5 | 2.0 | 2.0 | 2.0 | ~10.5 (*partly tonight) |
| P2 | 2.0 | 3.5 | 2.5 | 2.5 | 1.0 | ~11.5 |
| P3 | 0.75 | 3.0 | 2.0 | 2.5 | 2.0 | ~10.25 |
| P4 | 1.5 | 2.5 | 1.5 | 2.5 | 2.5 | ~10.5 |

Remainder = lunch, buffer, integration debugging — matching the spec's 32–36 productive-hour reality.
