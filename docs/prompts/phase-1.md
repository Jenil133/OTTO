# Phase 1 — UI Shell on Mock Data + Hour-Zero Foundations

## Goal
The complete Otto UI exists and **plays a full scripted demo run on mock events** — orb, transcript, 3 agent panes animating, Band feed scrolling, memory pills, cost meter ticking — with zero backend and zero sponsor keys. In parallel, the repo/backend skeleton exists, a hello-world is live on Render, every sponsor key is collected and verified, and the RocketRide go/no-go is decided. When this phase is done, all four people can build in parallel against frozen contracts.

## Window & Gate
- **UI track (Tasks A–D): can start TONIGHT (July 24)** — fully key-independent.
- Foundation track (Tasks E–G): Sat 9:00–9:45.
- **Gate @ 9:45:** keys verified, RocketRide decision made, contracts frozen. UI plays the full mock run by **11:00 latest** (runs in parallel with Phase 2).

## Scope
- **In scope:** All UI screens (Ask idle / Ask live / Results / Memory; Watches + Connect as static low-priority), mock event engine, event contract freeze, FastAPI skeleton, Render hello-world, §13 verification checklist, env-var vault.
- **Out of scope (later phases):** any real LLM/agent call, voice, real WebSocket data, mem0/Band/Respan integration.

## Prerequisites & Dependencies
- The 8 mockup images + design token sheet (in hand).
- Spec §5 data contracts.
- Foundation track needs sponsor credit/access codes distributed at 9:00.

## Tech, Tools & Components
React (Vite) + plain CSS variables (no Tailwind build, flat design = fast) · Python 3.11 + FastAPI + uvicorn · Render (one web service + static site) · Git monorepo: `otto/frontend`, `otto/backend`, `otto/docs`.

## Parallel Track Map

| Person | Tasks | Where |
|---|---|---|
| Person 1 | A, B, C | Tonight + Sat morning |
| Person 2 | D, E | Tonight (D) + Sat 9:00 (E) |
| Person 3 | G (their half) | Sat 9:00–9:45 |
| Person 4 | F, G (their half) | Sat 9:00–9:45 |

---

## Task Breakdown

### Task A — App shell, design system & Ask-idle screen — **Person 1** — `[CODING ONLY]` — ~1.5h (start tonight)
- [ ] `npm create vite@latest` React app in `otto/frontend`; commit to repo.
- [ ] Create `tokens.css` with the design system (paste verbatim):
```css
:root {
  --canvas:#0A0E12; --card:#11161C; --border:#232B34;
  --accent:#2DD4A7;            /* teal = "Otto acted" — the ONLY accent */
  --text:#E8ECEF; --muted:#8A94A0;
  --working:#F5A623; --failed:#F0625D;
  --radius-card:10px; --radius-pill:999px;
  --s1:8px; --s2:12px; --s3:16px;
}
```
- [ ] Enforce the 5 design laws: one accent only · status is always a dot color (teal done / amber working / red failed / slate idle) · telemetry always mono 11px muted · flat everything (no gradients/shadows) · the orb is the only big element.
- [ ] Left nav: Ask · Runs · Watches · Memory · Connect (icons + labels, active state).
- [ ] Ask-idle screen (mockup: "Ask, and it's done"): centered orb, tagline, 3 suggestion chips, status footer (`memory · gateway ok · watch idle` dots).

### Task B — Ask-live screen (the money screen) — **Person 1** — `[CODING ONLY]` — ~2h (tonight/morning)
- [ ] Left column: transcript (user bubble gray, Otto bubble teal-tinted), hold-to-talk orb with 3 visual states (idle / recording / processing).
- [ ] Center: `<AgentPane>` ×3 — status dot, `agent 01 · stripe.com/jobs`, latest step line, progress bar, `step 4/6`, elapsed mono timer. Props-driven only.
- [ ] Right rail: `<BandFeed>` (mono scrolling ops lines), `<OttoKnows>` (preference pills with × delete), `<BudgetMeter>` (`48s / 90s` bar).
- [ ] Top bar: telemetry chip `$0.11 · 48s · 3 agents · respan`; footer status line (`Results card assembling…` / `speaking in ~12s`).
- [ ] Everything renders from a single `state` object — no fetching inside components.

### Task C — Results card + Memory screen — **Person 1** — `[CODING ONLY]` — ~1.5h
- [ ] Results view (mockup `req_1832`): spoken-answer card with replay button placeholder, results table (company / role / location / fit pill), sources line, "N preferences saved" chip, Ask-follow-up + Export CSV buttons (CSV can be client-side later).
- [ ] Memory screen: grouped sections (preferences / aliases / facts), each row shows source request id, `used N×`, delete icon; "+ add memory" button; "edits apply on next request" subtitle.
- [ ] (LOW PRIORITY — only if ahead) static Watches + Connect screens from mockups; otherwise placeholder pages.

### Task D — Mock event engine + CONTRACT FREEZE — **Person 2** — `[CODING ONLY]` — ~1.5h (tonight)
- [ ] Define the single event type in `frontend/src/events.js` AND `docs/CONTRACTS.md`: `{"type": "plan|band_msg|agent_update|agent_screenshot|result|telemetry|memory_update", "payload": {...}, "ts": ...}` plus the Plan, AgentResult, mem0, Band shapes from spec §5. **This is the freeze — all four people build against this file.**
- [ ] Build `mockRun.js`: replays a scripted ~60s job-hunt run — t0 `plan` (3 subtasks) → `band_msg` from planner → interleaved `agent_update` streams (agent 2 finishes at 41s with 5 roles; agent 3 slower) → one `agent_screenshot` → `telemetry` tick every 5s → `result` (card + spoken text) → `memory_update` (2 prefs saved).
- [ ] UI consumes mock via the same interface as the future real WS (`?mock=1` toggle). This mock IS the cached-fallback foundation for demo night.
- [ ] Acceptance: pressing "run mock" animates the entire Ask-live screen end to end.

### Task E — Backend skeleton + adapter pattern — **Person 2** — `[CODING ONLY]` — ~1h (Sat 9:00)
- [ ] FastAPI app: `POST /task`, `WS /events` (broadcast hub), `GET /status/:id`, `POST /watch` stub. In-memory dicts only — no DB.
- [ ] `adapters/` package: base class with `mock: bool` flag; stub adapters for retriever, kimi, minimax, mem0, band, respan, elevenlabs — each returns canned data in mock mode. The spine must run on any subset of live keys.
- [ ] `.env.example` listing every key name.
- [ ] Create `backend/prompts/` (planner, synthesizer, personality, watch-compare — filled in Ph2–Ph4) and `docs/prompts/` (build prompts given to coding agents, incl. these phase files). **Rule from here on: every prompt gets committed — this is the PDD evidence trail judges will ask for.**

### Task F — Render deploy + env vault — **Person 4** — `[PLATFORM WORK ONLY]` — ~0.75h (Sat 9:00)
- [ ] Render account, connect repo, deploy backend hello-world as a web service; deploy frontend as static site (or serve from backend — pick one, note it in README).
- [ ] Enter all collected keys as Render env vars; local `.env` distributed to team (never committed).
- [ ] Confirm public URL loads on a phone over hotspot.

### Task G — Hour-zero verification checklist (§13) — **Person 3 + Person 4** — `[PLATFORM WORK ONLY / NO-CODE]` — ~0.75h, **BLOCKING**, Sat 9:00–9:45
Split and fill `docs/VERIFY.md`:
- [ ] **Person 3:** Retriever — API shape (submit/poll vs webhook), concurrency limit on hackathon credits, is a live session view embeddable? · TokenRouter — base URL, exact Kimi K3 model string, JSON-mode flag, context-caching flag · MiniMax — endpoint + image-input format.
- [ ] **Person 4:** ElevenLabs — agent tool/webhook mechanism + **timeout ceiling** + widget vs React SDK path · Respan — which providers route through it (Kimi? MiniMax?) · Band — SDK language + one minimal post-message call · mem0 — hosted vs self-host decision + add/search calls.
- [ ] **Person 2 + 3 (10 min):** skim RocketRide quickstart → **GO only if** JSON schema is clean AND steps can call an external tool/custom function AND custom model base URL is configurable. Record GO/NO-GO in VERIFY.md. NO-GO fallback = Standing Watch as the RocketRide pipeline (Phase 4).
- [ ] Announce all decisions to the room at 9:45. Nothing is guessed — anything unverifiable stays flagged.

---

## Deliverables / Definition of Done
`otto/` monorepo · full UI navigable with Ask-live animating a complete mock run · `docs/CONTRACTS.md` frozen · FastAPI skeleton with mock adapters · hello-world live on Render with env vars set · `docs/VERIFY.md` complete incl. RocketRide GO/NO-GO.

## Acceptance Criteria / How to Verify
Open deployed (or local) frontend with `?mock=1` → press run → watch a believable 60s Otto run play with zero backend. `curl POST /task` on Render returns a stub response. Every §13 line in VERIFY.md has an answer or an explicit "unknown — fallback chosen".

## Risks & Mitigations
1. **UI scope creep (6 screens).** → Build order is A→B→C strictly; Watches/Connect are static or skipped. The demo needs Ask-live + Memory, nothing else.
2. **Credit/key delays (access form went out late).** → Mock adapters mean nobody is blocked; keys slot in whenever they arrive.
3. **RocketRide skim inconclusive.** → Default is NO-GO. Ambiguity = no; the fallback slot is pre-planned.

## Estimated Effort
P1 ≈ 5h total but ~3h can happen tonight · P2 ≈ 2.5h (1.5 tonight) · P3 ≈ 0.75h · P4 ≈ 1.5h.

## Handoff to Next Phase
Frozen contracts + mock-driven UI mean Phase 2 builders (planner, Retriever, Band) plug real data into an already-working screen instead of building blind. VERIFY.md answers dictate the exact integration patterns Phase 2–3 use.
