# OTTO — Architecture & Flow Diagrams (Agent-Readable, Text-Only)

Purpose: give any coding agent (or teammate) the full structural picture in plain text.
These are the normative flows. On field names, `docs/CONTRACTS.md` wins.

**Legend**
```
──►   solid arrow  = critical request path (blocks the run)
╌╌►   dotted arrow = side channel (observe / augment / async — never blocks)
[GO?] = conditional on the hour-zero decision in VERIFY.md
★     = demo territory
```

**Cross-reference map**

| Diagram | Shows | Spec § | Built in |
|---|---|---|---|
| D1 | System component map | §4 | Ph1–Ph4 |
| D2 | Request lifecycle + latency budget | §6 | Ph2–Ph3 |
| D3 | ElevenLabs tool round-trip fallback ladder | §4.2, §10.1 | Ph3-B |
| D4 | One event stream → UI panels | §4.1, §5 | Ph1-D, Ph2-E |
| D5 | Three-zone access model | §3 | scope rule, all phases |
| D6 | Adapter / mock-mode pattern | §10.4, §13 | Ph1-E |
| D7 | Failure & fallback decision tree | §6, §7 | Ph2-A/C, Ph4-E |
| D8 | Build timeline + gates | §8 | all |
| D9 | Repo & deploy topology | §4.10 | Ph1-E/F, Ph3-D |
| D10 | Standing Watch loop | §4.11 | Ph4-D |

---

## D1 — System Component Map (who exists, where, and who talks to whom)

```
 ┌───────────┐   voice     ┌───────────────────┐  audio ws   ┌─────────────────────┐
 │    YOU    │◄───────────►│   OTTO WEB APP    │◄───────────►│  ELEVENLABS AGENT   │
 │ push-to-  │             │  (single page ★)  │             │ conversational      │
 │ talk only │             │ transcript · orb  │             │ STT + TTS +         │
 └───────────┘             │ 3 viewports       │             │ tool: run_task()    │
                           │ band feed · memory│             └──────────┬──────────┘
                           │ panel · $ meter   │                        │
                           └─────────┬─────────┘                        │ POST /task
                                     │ WS /events                       │ (tool call)
                                     │ (ONE typed stream, see D4)       │
                                     ▼                                  ▼
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │                 RENDER CLOUD — FastAPI backend (in-memory, no DB)                │
 │        POST /task · WS /events · GET /status/:id · POST /watch                   │
 │                                                                                  │
 │  ┌── ROCKETRIDE PIPELINE — one JSON file [GO?] ────────────────────────────────┐ │
 │  │                                                                             │ │
 │  │   [1] PLAN ───────────► [2] DISPATCH ───────────► [3] SYNTHESIZE            │ │
 │  │   Kimi K3 · JSON mode   fan out ×3 to             MiniMax M3 · merges       │ │
 │  │   context caching       Retriever (async          ok/partial/failed →       │ │
 │  │   + mem0 read           gather, 60s cap)          spoken ≤3 sent. + card    │ │
 │  │                                                                             │ │
 │  │   NOTE: voice edge (ElevenLabs loop) stays OUTSIDE this pipeline —          │ │
 │  │   latency-critical, per spec placement rule.                                │ │
 │  └────────┬─────────────────────┬──────────────────────────┬──────────────────┘ │
 └───────────┼─────────────────────┼──────────────────────────┼────────────────────┘
             │ LLM calls [1]+[3]   │ browser tasks [2]        │
             ▼                     ▼                          │
   ┌───────────────────┐  ┌────────────────────┐              │
   │  RESPAN GATEWAY   │  │  RETRIEVER CLOUD   │              │
   │ every LLM call    │  │  3 parallel        │              │
   │ exits here →      │  │  sessions          │              │
   │ cost + latency    │  └─────────┬──────────┘              │
   │ telemetry         │            ▼                         │
   └───────────────────┘  ┌────────────────────┐              │
                          │   LIVE WEBSITES    │              │
                          │  Zone-1 allowlist ★│              │
                          └────────────────────┘              │
                                                              │
  SIDE SERVICES (dotted — never on the critical path):        │
                                                              │
   ┌────────┐  read before [1]                                │
   │  mem0  │◄╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
   │ prefs  │◄╌╌ write after [3] (async, off critical path) ╌╌┘
   └────────┘
   ┌───────────┐  every actor (planner, webagent-1/2/3, synthesizer)
   │ BAND ROOM │◄╌╌ posts lifecycle msgs ╌╌╌► mirrored to UI feed rail
   │ otto-ops  │     persistent identities · audit log = trust pitch
   └───────────┘
```

---

## D2 — Request Lifecycle (sequence + latency budget, target 60–90s total)

```
 t≈0s    YOU speak (push-to-talk) ──► ElevenLabs STT
 t≈2s    OTTO ACKS IN VOICE: "On it — checking three sites"   ← perceived-zero wait
            │
            ▼
 t≈3s    mem0 READ (~1s) — semantic search: prefs, constraints, aliases
            │
            ▼
 t≈4s    KIMI K3 PLAN (5–10s) — strict JSON · max 3 subtasks · allowlist-only
            │                    read-only actions · success criteria per subtask
            ├──────────────────┬──────────────────┐
            ▼                  ▼                  ▼
 t≈12s   AGENT 1            AGENT 2            AGENT 3          ← Retriever sessions
         stripe.com/jobs    anthropic.com/…    databricks.com/…   run in PARALLEL
            │                  │                  │               30–60s, HARD CAP 60s
            │                  │                  │               never wait for the
            └────────┬─────────┴─────────┬────────┘               slowest — partials OK
                     ▼                   
 t≈70s   MINIMAX M3 SYNTHESIZE (5–8s)
         merge ok/partial/failed → spoken answer ≤3 sentences + results card
         (if data empty but screenshot exists → multimodal read of screenshot)
            │                     ╲
            ▼                      ╲ async, off the critical path
 t≈78s   TTS OUT (1–2s)             ╌╌╌► mem0 WRITE (durable prefs only)
         Otto speaks the answer
            │
 t≈80s   DONE.  Dead-air rule: if agents run long, Otto narrates
         ("two agents are still reading — one moment") and viewports keep eyes busy.
```

---

## D3 — ElevenLabs Tool Round-Trip: the Fallback Ladder (day's #1 risk)

```
 HOUR-ZERO QUESTION (VERIFY.md): what is the tool-call timeout ceiling?
 Our pipeline takes 60–90s. Pick EXACTLY ONE pattern. Implement one, stub none.

 PATTERN 1 — direct wait            (use if ceiling ≥ 90s — simplest)
   agent ──run_task(desc)──► POST /task ──[full pipeline 60–90s]──► result text
                                                                    └──► agent speaks

 PATTERN 2 — dispatch + poll        (use if ceiling too low)
   agent ──dispatch_task(desc)──► POST /task returns {request_id} IMMEDIATELY
   agent ──check_result(id)─────► GET /status/:id   (agent polls, narrates while waiting)
        …repeat until status=done──► result text ──► agent speaks

 PATTERN 3 — server push            (if SDK supports contextual update / msg injection)
   agent ──dispatch_task(desc)──► backend runs pipeline
   backend ╌╌ when done ╌╌► inject result into the live agent session ──► agent speaks

 LAST RUNG (always available — pre-built in Phase 2, kept forever):
   typed input box ──► POST /task ──► answer text ──► TTS voice OUTPUT only
   "the soul survives": Otto still speaks even if voice input is cut.
```

---

## D4 — One Event Stream → UI Panels (the contract that decouples the 4 builders)

```
 BACKEND ═══════════ WS /events · single typed stream ═══════════► FRONTEND
          emits {"type": ..., "payload": {...}, "ts": ...}

   type                feeds this UI element
   ─────────────────   ─────────────────────────────────────────────────────────
   plan            ──► transcript line ("3 agents dispatched") + pane setup
                       (titles, target urls, pane count)
   agent_update    ──► viewport pane N: latest step line · progress bar ·
                       "step x/6" · elapsed timer · status dot amber
   agent_screenshot──► viewport pane N: still image (fallback visual, D1 note)
   band_msg        ──► right rail ops feed (mono lines, autoscroll)
   telemetry       ──► top chip "$0.11 · 48s · 3 agents · respan" + budget bar
   result          ──► results card (table + fit pills + sources) + Otto bubble
                       + footer status line; done panes → dot teal / failed red
   memory_update   ──► "otto knows" pills (+ "N preferences saved" chip)

 RULES:
 · UI renders ONLY from this stream — no component fetches anything itself.
 · Mock engine (?mock=1) replays a recorded stream through the SAME pipe →
   identical UI. The recorded golden run + hotkey = demo-night safety net.
 · Unknown event types are logged, never crash the UI.
```

---

## D5 — Three-Zone Access Model (governs ALL scope decisions)

```
 ┌─ ZONE 1 · OPEN WEB ★ ───────┐ ┌─ ZONE 2 · CONNECTABLE ──────┐ ┌─ ZONE 3 · DEAD ZONE ───────┐
 │ mechanism: HANDS            │ │ mechanism: KEYS             │ │ mechanism: NONE            │
 │ (Retriever cloud browsers)  │ │ (official OAuth APIs)       │ │ no public API · fights     │
 │ no permission needed        │ │ one scoped handshake each   │ │ automation · ToS-hostile   │
 │                             │ │ revocable · every action    │ │                            │
 │ · careers pages             │ │ logged (Band audit)         │ │ · LinkedIn (canonical)     │
 │ · HN "Who's Hiring"         │ │ · Gmail  (stretch, burner   │ │                            │
 │ · shopping / travel         │ │   acct, read/draft only)    │ │ OTTO DECLINES THESE —      │
 │ · public listings           │ │ · Calendar · Notion · Zoom  │ │ honestly named in pitch,   │
 │                             │ │                             │ │ never faked                │
 │ THE DEMO LIVES HERE         │ │ ◐ at most ONE connector,    │ │                            │
 │                             │ │ late, only if someone has   │ │                            │
 │                             │ │ done Google OAuth before    │ │                            │
 └─────────────────────────────┘ └─────────────────────────────┘ └────────────────────────────┘
 Litmus test for any service: search "[service] API"
   → developer portal with OAuth = Zone 2 · nothing = Zone 3
 Pitch scale answer: "reach grows one handshake at a time — MCP-style connectors;
 the layer sponsor Nexla builds for 700+ enterprise systems" (name-check only).
```

---

## D6 — Adapter / Mock-Mode Pattern (why nobody is ever blocked)

```
                       ┌──────────────────────────────────┐
  ORCHESTRATOR ───────►│   adapters/<sponsor>.py          │
  (never calls any     │                                  │
   sponsor directly)   │   if MOCK flag or key missing ───┼──► canned response (instant)
                       │   else ─────────────────────────►┼──► real sponsor API
                       └──────────────────────────────────┘
    one adapter each:  retriever · kimi · minimax · mem0 · band · respan · elevenlabs

  WHY: credits arrived late + integrations flake → the spine must run on ANY
  subset of live keys. Flip adapters to real one at a time; a broken sponsor
  flips back to mock in seconds. Same trick powers ?mock=1 and the golden replay.
```

---

## D7 — Failure & Fallback Decision Tree (runtime + stage)

```
                       plan JSON valid (pydantic)?
                       ├─ NO ──► Otto ASKS a clarifying question aloud. Never crash.
                       └─ YES
                            │  dispatch agents (60s hard cap each)
                            ▼
                  how many returned ok / partial?
                  ├─ ALL FAILED ──► honest spoken failure + Band feed shows the
                  │                 attempts — "even failure looks alive"
                  ├─ SOME ok ─────► synthesize on partials; Otto SAYS one failed
                  └─ ALL ok ──────► full comparison answer + results card
                            │
              ══ STAGE LAYER (demo night) ══
                            │
              live run stalls or flakes on stage?
              └─► operator hits GOLDEN-RUN HOTKEY — replays the recorded event
                  stream through D4's pipe; presenter narrates without breaking
                  stride.  Absolute last resort: backup VIDEO recorded ~6:30PM.
              defense depth: live run ──► hotkey replay ──► video. In that order.
```

---

## D8 — Build Timeline + Gates (phases over the Saturday clock)

```
 9a       9:45          12:30/1p           3p               6p       7:30p      9p
 ├─ PH1 ─┤◄─── PH2 ────►│◄───── PH3 ─────►│◄───── PH4 ─────►│◄─ PH5 ─►│◄─ DEMOS ─►│
 setup +   TEXT SPINE      FAN-OUT ×3        mem0 · respan     rehearse   3 beats
 verify    (1 agent,       + VOICE LOOP      rocketride[GO?]   ×5 ·       on stage
 UI-on-    typed input)    + DEPLOY NOW      watch? · harden   video ·
 mock                                                          pitch
 (UI can start TONIGHT — key-independent)

    ▲            ▲                ▲                 ▲
  GATE 9:45    CP1 12:30-1p     CP2 3p            18:00 FEATURE FREEZE
  keys done    spine e2e OR     one full voice    hard stop — nothing
  contracts    simplify NOW —   run works on      new after, ever
  frozen       never build on   the DEPLOYED
  RR GO/NO-GO  a broken spine   build

 CUT ORDER if behind:  EdgeOne → Watch → RocketRide → 3rd agent → Band → voice INPUT
 NEVER CUT:            fan-out visual · spoken answer · memory beat
```

---

## D9 — Repo & Deploy Topology

```
 GIT MONOREPO  otto/
 ├─ frontend/                React (Vite) + tokens.css
 │    src/events.js          ← FROZEN event contract (D4)
 │    src/mockRun.js         ← mock engine + golden-run replay (hotkey)
 │            └────────────────────────────► RENDER STATIC SITE
 │                                           (or served by backend — pick ONE, doc it)
 ├─ backend/                 FastAPI
 │    adapters/              one per sponsor, mock-mode (D6)
 │    pipeline/              plan · dispatch · synthesize (plain-code path)
 │    rocketride.json        [GO?] same 3 steps as one pipeline file;
 │            │              model base URLs → Respan gateway
 │            └────────────────────────────► RENDER WEB SERVICE
 │                                           env vars = ALL sponsor keys (never in git)
 └─ docs/
      CONTRACTS.md  frozen @9:45 · VERIFY.md  hour zero · ALLOWLIST.md  Ph2-B

 optional: Render CRON ── Standing Watch loop (D10)
 optional: Tencent EdgeOne static mirror — FIRST thing on the cut list
 rule: current build deployed by ~3PM (CP2). Deploy problems at 3PM = chore; at 7PM = fatal.
```

---

## D10 — Standing Watch Loop (stretch, Phase 4-D)

```
 "Otto, watch [page] and call me when [condition]"
     │ voice → plan → POST /watch
     ▼
 store {url, condition, contact_mode}          (in-memory)
     │
     ▼  every N min (Render cron / interval loop)
 ONE Retriever check on url ──► one small model call: "condition met?"
     ├─ NO ──► sleep · repeat · watch card shows "watching · last check Xm ago"
     └─ YES ─► TRIGGER:
                simplest stage version: Otto proactively SPEAKS in the open session
                (ElevenLabs outbound call only if trivially available)
                watch card flips to "triggered HH:MM · view run"

 DEMO RULE: never wait for reality on stage — the UI "simulate trigger" button
 fires the YES branch directly.
 [GO?] tie-in: if RocketRide was NO-GO for the main brain, implement THIS loop as
 the RocketRide pipeline (fetch → compare → notify) — the honest fallback integration.
```

---

*Feed order for a coding agent: README-master-plan.md → this file → the phase file it is executing. Diagrams are normative for flow and sequencing; `docs/CONTRACTS.md` is normative for exact field names.*
