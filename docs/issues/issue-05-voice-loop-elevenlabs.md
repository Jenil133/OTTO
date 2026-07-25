# Wire the ElevenLabs conversational voice loop

**Route:** pdd-change · **Phase:** 3-B · **Owner:** Person 1 + Person 2 (pair, 90-min timebox) · **Status: OPEN**

## Goal

Press-to-talk a spoken request → Otto verbally acks within 2 seconds → the request runs the existing spine via `POST /task` → Otto speaks the merged answer — with the typed box untouched as the permanent fallback.

Where: ElevenLabs console (conversational agent + `run_task` tool) + `frontend/` (widget or React SDK embed in the transcript column) + `backend/adapters/elevenlabs.py` (currently a mock-only stub, `KEY_NAME = "ELEVENLABS_API_KEY"`). The tool round-trip pattern is the **hour-zero D3 decision** recorded in `docs/VERIFY.md` (Person 4 section) — implement exactly ONE of: (1) tool waits 60–90s, (2) `dispatch_task` + `check_result` polling pair against `GET /status/:id`, (3) backend-initiated contextual update. Stub none.

## Acceptance criteria

- **Given** the deployed build over hotspot, **when** the user push-to-talks a jobs request, **then** the agent gives a spoken ack **≤2s** and the backend log shows the `run_task` tool hitting `POST /task` (CONTRACTS.md §6 row 1) with the transcribed text.
- **Given** the run completes, **when** the `result` event lands, **then** Otto speaks a ≤3-sentence answer and the spoken text mirrors into the transcript bubbles.
- **Given** the D3 polling pattern is chosen, **when** the tool polls, **then** `GET /status/:id` answers `running | done | failed` per §6 — it already returns `"unknown"` instead of 404 precisely so the poll loop needs no error branch (`backend/main.py`).
- **Given** the mic is denied, the widget fails to load, or voice misbehaves on stage, **when** the user types instead, **then** the full typed spine works unchanged (Ask-idle and Ask-live input boxes).
- **Given** agents run long, **when** dead air threatens, **then** the agent narrates ("two agents are still reading — one moment") per its personality prompt.

## Must not

- Must not remove, hide, or regress the typed input path — voice is additive, typed is the demo fallback.
- Must not open-mic: push-to-talk only, wired to the on-screen orb.
- Must not put the ElevenLabs API key or any secret in the widget config, frontend bundle, or committed files — agent-side secrets live in the ElevenLabs console / Render env only.
- Must not run the voice edge inside the pipeline — STT/TTS stay outside (D3 latency-critical placement, `elevenlabs.py` module docstring).
- Must not break `?mock=1` or hotkey `g`.
- Past the 90-min pair timebox, must not keep debugging: fall back to typed input + voice **output** (backend sends result text to TTS).

## Evidence

- `backend/adapters/elevenlabs.py`: stub adapter, mock returns `audio_ref: null` — the flip point.
- `docs/VERIFY.md` Person 4: the three unanswered ElevenLabs lines (tool mechanism, timeout ceiling, widget vs React SDK) — answered at the 9:45 gate, they select the D3 pattern.
- `backend/main.py`: `POST /task` already returns `{request_id, status:"accepted"}` immediately (dispatch+poll ready); `GET /status/:id` poll-safe.
- `phase-3 (1).md` Task B: personality prompt content, fallback ladder, and the pairing plan.

## Validation

```
cd backend && .venv/bin/python -m pytest tests/ -q     # existing suite stays green
cd frontend && npx vite build
# demo path (Checkpoint 2, 15:00): on the DEPLOYED URL over hotspot —
# push-to-talk "Find new-grad SDE roles at Stripe, Anthropic and Databricks"
# → spoken ack ≤2s → panes run → Otto speaks the comparison.
# fallback check: type the same request → identical run.
```

## Done when

- [ ] One full voice run works on the deployed build (CP2 gate).
- [ ] Positive AND negative paths verified: voice run, typed fallback, dead-air narration, mic-denied.
- [ ] Issue, code, ElevenLabs agent config, and `docs/VERIFY.md` (D3 pattern recorded) agree.
- [ ] No secrets in the widget config, bundle, diff, or logs.
- [ ] Suite + build pass; nothing regressed.
- [ ] Exact CP2 demo flow works manually on the demo-corner setup.
- [ ] Linked PR passes checkup against this issue.
