# OTTO

Otto is a voice-first agent fleet: you speak a request once, Otto acks in
about two seconds, plans it into at most three read-only web subtasks, fans
them out to parallel cloud-browser agents, and speaks back a synthesized
answer with a results card — while one typed event stream drives every panel
of the ops-console UI (orb, agent viewports, Band feed, memory pills, cost
meter). Mock mode replays the same stream with zero backend, so the demo
never depends on a flaky integration.

## Repo map (architecture D9)

```
otto/
├─ frontend/     React (Vite) + tokens.css — the single-page ops console
│    src/events.js   FROZEN event contract (mirror of docs/CONTRACTS.md §1)
│    src/mockRun.js  mock engine + golden-run replay
├─ backend/      FastAPI skeleton — POST /task · WS /events · GET /status/:id · POST /watch
│    adapters/       one per sponsor, mock-mode pattern (D6)
│    prompts/        runtime prompts (planner · synthesizer · personality · watch-compare)
└─ docs/         CONTRACTS.md (frozen) · VERIFY.md (hour zero) · ALLOWLIST.md · prompts/ (PDD trail)
```

## Run the frontend

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173/?mock=1 — the full UI runs on mock events, no
backend needed. Hotkey `g` fires the golden-run replay (the demo-night safety
net); add `?speed=4` to fast-forward the scripted 60s run.

## Run the backend

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

In-memory skeleton — `GET /` answers the hello-world probe; routes follow
`docs/CONTRACTS.md` §6. Copy `.env.example` to `.env` for keys; missing keys
degrade adapters to mock automatically (`OTTO_MOCK=1` forces mock globally).

## Deploy

Render: backend as a web service (env vars hold all sponsor keys — never in
git), frontend as a static site — or served from the backend; that decision
is pending Phase 1 Task F and will be recorded here.

## Contracts

`docs/CONTRACTS.md` is FROZEN — all builders code against it. On field-name
conflicts it wins; `architecture-diagrams.md` wins for flow.
