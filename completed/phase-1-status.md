# Phase 1 — Status (as of Fri July 24 night)

## ✅ Completed

### UI track (Tasks A–D) — DONE, verified in browser
- **Task A — App shell + design system + Ask-idle**: Vite React app in `frontend/`, `tokens.css` verbatim, 5 design laws enforced, left nav (Ask · Runs · Watches · Memory · Connect), Ask-idle screen (orb, "Ask, and it's done", 3 chips, status footer).
- **Task B — Ask-live (money screen)**: transcript bubbles, hold-to-talk orb (3 states), 3× `<AgentPane>` (dot, step line, progress, elapsed timer, screenshot fallback), `<BandFeed>` / `<OttoKnows>` / `<BudgetMeter>` right rail, telemetry top chip, footer status line. Everything renders from one `state` object.
- **Task C — Results + Memory**: spoken-answer card + replay placeholder, results table with fit pills + source links, "2 preferences saved" chip, Ask-follow-up + working client-side Export CSV. Memory screen: 3 sections, `req id · used N×`, live delete, search, + add memory. **Bonus: Watches + Connect built too (were low-priority).**
- **Task D — Mock engine + CONTRACT FREEZE**: `frontend/src/events.js` + `docs/CONTRACTS.md` frozen (all 7 event types + Plan/AgentResult/mem0/Band shapes + `recall` field). `mockRun.js` replays scripted 62s run — agent 2 done at 41s w/ 5 roles, screenshot event, telemetry ticks, result, memory beat. Hotkey `g` = golden replay, `?speed=N`, `?mock=1` pipe identical to future WS.
- **Acceptance met**: run mock → entire Ask-live animates end to end → auto-advances to Results. Zero console errors.

### Foundation track (code parts of Task E) — DONE
- FastAPI skeleton: `POST /task`, `WS /events` broadcast hub, `GET /status/:id`, `POST /watch`, in-memory only.
- `adapters/` with mock-mode base class + 7 stub adapters (retriever, kimi, minimax, mem0, band, respan, elevenlabs) returning canned CONTRACTS-shaped data.
- `.env.example` with every key name. `backend/prompts/` + `docs/prompts/` PDD trail created (phase files copied in).
- `docs/VERIFY.md` checklist **template**, `docs/ALLOWLIST.md` stub, root `README.md`, `.gitignore`.

**Run:** `cd frontend && npm run dev` → http://localhost:5173/?mock=1 (deps already installed).

## ⏳ Pending (Sat morning — need humans/keys/accounts)

- **Git**: `git init`, first commit, push to GitHub (owner doing this Sat morning).
- **Task E remainder**: nothing code-wise; real adapter `_real()` impls are Phase 2 by design.
- **Task F (Person 4)**: Render account, deploy backend hello-world + frontend static site, enter env vars, phone-hotspot test. ~0.75h.
- **Task G (Persons 3+4, BLOCKING, 9:00–9:45)**: fill `docs/VERIFY.md` answers — Retriever/TokenRouter/MiniMax (P3), ElevenLabs timeout ceiling/Respan/Band/mem0 (P4), RocketRide GO/NO-GO skim (P2+P3). Announce at 9:45.
- **Gate @ 9:45**: keys verified, RocketRide decision recorded, contracts confirmed frozen → all four build in parallel on Phase 2.

## Notes for the team
- Contract change after 9:45 = tell all four people out loud. `docs/CONTRACTS.md` wins on field names.
- Design-law exemption documented in `tokens.css`: mono telemetry may use teal for live-data emphasis ("accent data → teal" per token sheet).
- Mock engine doubles as the demo-night golden-run fallback (D7): live run → hotkey `g` replay → backup video.
