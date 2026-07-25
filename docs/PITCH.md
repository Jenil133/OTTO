# OTTO — Pitch Pack (Phase 5-C)

**Event:** Build Fast. Launch Loud. — a PDD hackathon · demo slots 19:30–21:00 Sat.
**Roles:** Person 4 presents (best speaker) · Operator owns hotkey `g` · Timer enforces the clock.
**Stage rule (D7):** exactly ONE live run per beat · defense depth: live run → `g` golden replay → backup video. In that order.

---

## 1 · The 10-second opener — pick one, say it verbatim

**A (anchor):** "Claude Code, but pointed at the open web instead of your codebase — and it doesn't need you in the room."

**B (demo-first):** "You're about to watch three browsers hunt the web at the same time. And when they're done, Otto doesn't hand you tabs — Otto talks back."

**C (short):** "You say it once. Three agents fan out. Otto answers in three sentences — and remembers you next time."

*(If the 3rd agent got cut: every "three" becomes "a fleet of browsers" — never promise a count the screen won't show ten seconds later.)*

---

## 2 · The three demo beats (never cut: fan-out visual · spoken answer · memory beat)

**Clock (5:00 slot): opener 0:10 · Beat 1 1:30 · Beat 2 1:15 · Beat 3 0:45 · close 0:20 = 4:00, keeping 60s slack for live-run variance. §3–§5 are Q&A ammunition, never stage time. If any beat overruns, Beat 3 dies first.**

### Beat 1 — Job-hunt fan-out ×3 (cold open, no slides first — the fan-out IS the hook)
- **Audience sees:** push-to-talk ask → plan card "3 agents dispatched" → three live viewports reading careers pages **in parallel** → results card with fit pills → Otto SPEAKS ≤3 sentences. Cost chip on screen.
- **Presenter says:** "One sentence from me. Three browsers working at once — hands off the keyboard." *(and hands are demonstratively off the keyboard.)*
- **Timing:** ~90s. Pipeline budget is 60–90s (D2); if agents run long, Otto narrates the dead air — that's designed, not a stall.
- **If voice input flakes (or got cut):** type the ask in the AskIdle input — the fan-out visual and the spoken answer are untouched (D3: the soul survives). Rehearse the typed cold-open once so it isn't a scramble.
- **If it stalls:** operator hits `g` — the golden run replays through the SAME event pipe. **If `g` fires, the presenter SAYS SO in the same breath — "that's our safety net, watch the request id" — never silently.** Absolute last resort: backup video, local on this laptop.

### Beat 2 — Memory (the trust beat)
- **Audience sees:** second ask — "now check Figma and Notion" — recall pills ("new-grad", "bay area") light up at t≈1s, Otto says "Bay Area only, like last time" **unprompted**. Then: open the memory panel, DELETE a pill live — the next answer changes.
- **Presenter says:** "I never repeated myself. Otto remembered — and watch, I can make it forget."
- **Timing:** ~75s including the live delete.
- **If it stalls:** `g` replay still shows the recall pills and spoken callback; skip the live delete in replay mode — never fake a delete that didn't happen.
- **Target note:** Figma and Notion are unscored candidates until Task B runs — if either gets cut, swap the ask to two surviving allowlist sites. The recall pills are the beat, not the targets.

### Beat 3, variant A — Standing Watch (NOT YET BUILT: Watches.jsx is static Phase-1, no simulate control exists. Variant B is the default until the Ph4 watch pipeline AND the simulate trigger are built and survive one clean rehearsal.)
- **Audience sees:** "Otto, watch this page and tell me when it changes" → watch card "watching · last check 0m ago" → operator fires **simulate trigger** (D10 demo rule: never wait for reality on stage) → card flips to "triggered" → Otto proactively SPEAKS.
- **Presenter says:** "You hung up two minutes ago. Otto didn't."
- **Timing:** ~45s. If the slot runs long: cut Beat 3 before cutting the close.

### Beat 3, variant B — Full voice loop (only if Ph3-B landed and rehearsed)
- **Audience sees:** the whole round trip by voice — push-to-talk ask → Otto acks in voice at t≈2s → fleet runs → Otto speaks the answer. Keyboard never touched.
- **Presenter says:** "No keyboard, no tabs. That entire thing was one sentence out loud."
- **If voice input flakes:** type the ask — Otto still SPEAKS the answer (D3 last rung: the soul survives).

---

## 3 · "Isn't this just X?" — the differentiation table

| vs | Their shape | Otto |
|---|---|---|
| Whisperflow + Claude Code | Voice is commodity STT; Claude Code acts on YOUR machine | Otto acts on the OPEN WEB — sites you don't own, no repo required |
| ChatGPT / Operator browsing | One agent, one site, while you sit and watch | Three agents at once — and still working after you hang up |
| LinkedIn-style walled gardens | Scraping theater or ToS fights | Otto DECLINES Zone-3 sites, out loud, never fakes (D5) |

**Two defendable moats: parallelism + persistence.** Everything else is commodity.

---

## 4 · The PDD story (say the theme's name, once)

- **The product runs on prompts:** spoken ask → planner prompt → three agent briefs the planner writes itself (prompts generating prompts) → synthesizer prompt. The code between them is dispatch plumbing.
- **The build ran on prompts:** the phase files in `docs/prompts/` WERE the prompt pack fed to coding agents. Prompt files are source; code is generated output.
- **Every prompt is a tracked artifact** — a judge who asks "show me your PDD" gets `PDD.md` and real files opened, not claims made. Until the push lands, say "committed to the repo we push this morning," never "committed."
- **DoD scored honestly: 5/7 at Friday close.** The two ⚠️s — CI and PR-checkup — unlock with Saturday's first GitHub push; re-score after the push and say the live number on stage. **Honesty is the pitch.**

---

## 5 · Sponsor beats — earned, not name-checked (never claim planned as live)

| Sponsor | The earned beat (one breath) | Status |
|---|---|---|
| **TokenRouter** | 5 planner models benchmarked live through ONE gateway + key: 28s → 2.8s, a 10x win; swap = one env var, zero code. Our strongest artifact. | **LIVE** |
| **Retriever** | "Prompt-driven web agents" is their own category name — our planner authors each agent's brief at runtime. | Fan-out ×3 landing today (Ph3) |
| **MiniMax** | M3 merges ok/partial/failed into speech + card, honesty paths included; multimodal screenshot-recovery branch stubbed. | **Synthesis LIVE** · recovery stub planned |
| **ElevenLabs** | Voice edge deliberately OUTSIDE the pipeline (D3) — latency-critical stays at the edge; typed-in / spoken-out survives any outage. | Ph3 today |
| **mem0** | Prefs read before planning, written after — the entire Beat 2 payoff. | Ph4 today |
| **Band** | `otto-ops` room: every actor posts lifecycle — the audit trail is the trust story. | Internal feed LIVE · real room today |
| **Respan** | Cost + latency telemetry on every LLM call → the on-screen $ meter. | Ph4 today |

---

## 6 · Numbers that land (all real — verifiable in the repo or live on the gateway dashboard)

- **16s** — live spine wall clock: typed ask → real planner → real synthesis → card over a real WebSocket (`req_cdbe2260`)
- **2.8s** — planner latency, down from 28.0s — **10x**, chosen by measured benchmark, not vibes (5/5 consistency runs)
- **every backend test green** with **zero keys, zero network** — 36 at Friday close, growing as fan-out tests land today; run `pytest -q` before the slot and say the live number
- **4** — bugs that ONLY live traffic could surface; all found and fixed same day
- **62s** — golden-run replay, byte-compatible with the real event stream
- **$50** — event credit; a request costs cents. Check the TokenRouter dashboard before the slot and quote the real remaining balance — a live number beats a stale adjective
- **117** — models in the catalog behind one key

---

## 7 · Hard Q&A — 2 lines max each, ≤20 seconds spoken

**"Why not just ChatGPT?"**
ChatGPT browses one site while you watch. Otto runs three at once and keeps working after you hang up — parallelism and persistence are the whole point.

**"What happens when a site blocks you?"**
A blocked agent returns an honest `partial` and Otto says so out loud — never fabricates a row. The allowlist itself is empirical: sites that fight automation get cut, not faked. *(Only add "we scored 8 candidates today" if Task B ran — check ALLOWLIST.md's viewport/phrasing columns are filled.)*

**"Is the demo canned?"**
A golden replay exists — we built our own safety net and we'll show you the hotkey. The tell is on screen: the canned run is always `req_1832`; live runs mint fresh ids like `req_cdbe2260`. Check the id on the card — and if we'd had to fall back tonight, we'd have told you before you asked.

**"How do you make money?"**
A full three-agent run costs cents — you watched the meter. We sell the fleet as a consumer subscription and Standing Watch per-watch; our COGS is on screen and it's coffee change, and model prices only fall. *(Only claim "the meter" if Respan telemetry landed; otherwise: "per the gateway dashboard, a run costs cents.")*

**"Privacy of the memory?"**
Every memory is a visible pill — explicit, per-user, deletable one at a time, and deleting one changes the next answer. Nothing is inferred silently: the panel you saw is the entire store. *(Drop "we deleted one on stage" if Beat 2 ran in replay mode. Have the mem0 hosted-vs-self-host answer ready — a judge will ask where the pills physically live.)*

**"Why voice at all?"**
Voice is the only interface that works when your hands and eyes are busy — and a fleet means Otto actually has something worth saying when it comes back.

**"What broke today?"**
Four live-only bugs: a temperature-param 400, an un-fenced `<think>` block corrupting JSON, reasoning-model timeouts, and a synthesizer over-reporting failures. All fixed in adapters — never by weakening a test.

**"Why isn't Kimi in the loop if Moonshot sponsors?"**
We benchmarked it: K3 plans correctly but takes 28s against a 5–10s budget. Reasoning models belong on latency-tolerant slots — it's our pick for the watch-compare stage, not the hot path.

**"What can't Otto do?"**
Zone-3 walled gardens — LinkedIn is the canonical case: no API, fights automation. Otto declines them by design; honesty over theater.

**"How does this scale past 8 sites?"**
Zone 1 grows by empirical allowlisting; Zone 2 grows one OAuth handshake at a time — MCP-style connectors, each one scoped, revocable, and logged.

---

## 8 · The close

**"Every assistant can talk. Otto has hands."**

Reach grows one handshake at a time — and what you watched ran on the open web, request ids on screen, cost meter running. *(If `g` fired at any point tonight, swap to: "and when one run needed our safety net, you saw us say so out loud — that honesty is the product.")* *(Then: the ask.)*
