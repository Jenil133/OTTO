"""OTTO backend skeleton — Phase 1 · Task E.

FastAPI app implementing the frozen HTTP surface of docs/CONTRACTS.md §6:

    POST /task           -> { request_id, status: "accepted" }
    WS   /events         -> stream of §1 envelope events
    GET  /status/{id}    -> { request_id, status, result }
    POST /watch          -> { watch_id, status: "watching" }
    GET  /               -> hello-world probe for the Render deploy (Task F)

Everything is IN-MEMORY — no DB (phase-1.md Task E). The real pipeline
(plan → dispatch → synthesize, architecture D1/D2) lives in
`pipeline.run_pipeline` (Phase 2 · Task D) and emits its events through
`emit()` below so the frontend never changes.

Run locally:
    cd backend && pip install -r requirements.txt
    uvicorn main:app --reload
"""

from __future__ import annotations

import asyncio
import secrets
import time
from typing import Any, Dict, Optional, Set

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()  # backend/.env — local dev; Render sets real env vars directly

from adapters.band import BandAdapter
from adapters.kimi import KimiAdapter
from adapters.mem0 import Mem0Adapter
from adapters.minimax import MinimaxAdapter
from adapters.retriever import RetrieverAdapter
from pipeline import run_pipeline

app = FastAPI(title="otto-backend", version="0.1.0")

#: The spine's sponsor adapters (D6). Each decides mock-vs-live itself off
#: its env key + OTTO_MOCK; `GET /` reflects the aggregate below.
ADAPTERS = (
    KimiAdapter(),
    RetrieverAdapter(),
    MinimaxAdapter(),
    Mem0Adapter(),
    BandAdapter(),
)

# Hackathon setting: allow every origin so the Render static site (or any
# localhost port) can hit the API without ceremony (architecture D9).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory stores (CONTRACTS.md §6 — no DB, resets on redeploy, that's fine)
# ---------------------------------------------------------------------------

#: request_id -> { "text": str, "status": "running|done|failed", "result": dict|None }
TASKS: Dict[str, Dict[str, Any]] = {}

#: watch_id -> { "url": str, "condition": str, "contact_mode": str, "status": "watching" }
WATCHES: Dict[str, Dict[str, Any]] = {}

#: Strong refs to in-flight pipeline tasks — the loop only holds weak refs, so
#: without this a run could be garbage-collected mid-flight (TASKS stuck on
#: "running", no result event). Discarded on completion.
BACKGROUND_TASKS: Set["asyncio.Task[Any]"] = set()


# ---------------------------------------------------------------------------
# WS /events — the ONE stream (CONTRACTS.md §1, architecture D4)
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Broadcast hub for `WS /events`.

    Keeps a set of live sockets; `broadcast()` fans one event dict out to all
    of them. Dead sockets are pruned on send failure. The UI renders ONLY
    from this stream (D4) — no component fetches anything itself.
    """

    def __init__(self) -> None:
        self.active: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a socket."""
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Forget a socket (already closed or about to be)."""
        self.active.discard(websocket)

    async def broadcast(self, event: dict) -> None:
        """Send one event dict to every connected socket, pruning dead ones.

        Iterates a snapshot (`list(...)`) so a client connecting mid-broadcast
        can't raise 'Set changed size during iteration' out of emit() and abort
        a healthy pipeline stage into the D7 crash-net.
        """
        dead: Set[WebSocket] = set()
        for ws in list(self.active):
            try:
                await ws.send_json(event)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def emit(type: str, payload: dict) -> None:
    """Wrap `payload` in the frozen envelope (CONTRACTS.md §1) and broadcast.

        { "type": "plan|band_msg|agent_update|agent_screenshot|result|telemetry|memory_update",
          "payload": {...}, "ts": <epoch ms> }

    Every Phase 2+ pipeline stage emits through this ONE helper so the mock
    engine (?mock=1) and the real stream stay byte-compatible (D4).
    """
    await manager.broadcast({"type": type, "payload": payload, "ts": int(time.time() * 1000)})


@app.websocket("/events")
async def events(websocket: WebSocket) -> None:
    """`WS /events` — the single typed stream of CONTRACTS.md §1.

    Clients only listen; anything they send is ignored (kept as a read loop
    so disconnects are detected promptly).
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # ignore inbound; detect disconnect
    except WebSocketDisconnect:
        pass  # normal client close
    except Exception:
        # Odd frames (e.g. a binary message makes receive_text raise KeyError)
        # must not leak a stale socket — fall through to disconnect below.
        pass
    finally:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# HTTP surface (CONTRACTS.md §6)
# ---------------------------------------------------------------------------


class TaskIn(BaseModel):
    """`POST /task` body — CONTRACTS.md §6."""

    text: str


class WatchIn(BaseModel):
    """`POST /watch` body — CONTRACTS.md §6, Standing Watch loop (D10)."""

    url: str
    condition: str
    contact_mode: str


@app.get("/")
def root() -> Dict[str, Any]:
    """Hello-world probe for the Render web service (phase-1.md Task F).

    `mock` reflects the D6 adapter state: True until at least one sponsor
    adapter is live (its key present and OTTO_MOCK unset).
    """
    return {
        "service": "otto-backend",
        "status": "hello-world",
        "mock": not any(a.live for a in ADAPTERS),
    }


@app.post("/task")
async def create_task(body: TaskIn) -> Dict[str, str]:
    """Accept a task — CONTRACTS.md §6 row 1.

    Returns `{request_id, status: "accepted"}` IMMEDIATELY (dispatch+poll
    pattern, architecture D3 Pattern 2), then launches the Phase 2 spine
    (`pipeline.run_pipeline`, Task D) in the background — events stream over
    `WS /events`, and the pipeline flips TASKS to done|failed itself (D7).
    """
    request_id = f"req_{secrets.token_hex(4)}"
    while request_id in TASKS:  # collision guard (rare, but cheap)
        request_id = f"req_{secrets.token_hex(4)}"
    TASKS[request_id] = {"text": body.text, "status": "running", "result": None}
    task = asyncio.create_task(run_pipeline(request_id, body.text, TASKS, emit))
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)
    return {"request_id": request_id, "status": "accepted"}


@app.get("/status/{request_id}")
def get_status(request_id: str) -> Dict[str, Any]:
    """Poll a task — CONTRACTS.md §6 row 3.

    `result` is the §1 `result` payload once done, else None. Unknown ids
    answer `status: "unknown"` rather than 404 so the voice agent's poll
    loop (D3 Pattern 2) never has to special-case errors.
    """
    task: Optional[Dict[str, Any]] = TASKS.get(request_id)
    if task is None:
        return {"request_id": request_id, "status": "unknown", "result": None}
    return {"request_id": request_id, "status": task["status"], "result": task["result"]}


@app.post("/watch")
def create_watch(body: WatchIn) -> Dict[str, str]:
    """Register a standing watch — CONTRACTS.md §6 row 4, architecture D10.

    Skeleton only stores `{url, condition, contact_mode}`; the check loop is
    Phase 4-D.
    """
    watch_id = f"w_{secrets.token_hex(2)}"
    WATCHES[watch_id] = {
        "url": body.url,
        "condition": body.condition,
        "contact_mode": body.contact_mode,
        "status": "watching",
    }
    return {"watch_id": watch_id, "status": "watching"}
