"""OTTO pipeline — orchestrator v1 (phase-2 Task D, architecture D1/D2).

The text spine, end to end::

    typed text -> mem0 read (stub []) -> Kimi K3 plan -> ONE Retriever
    subtask -> MiniMax synthesis -> `result` event + TASKS store

Every stage emits through the ONE envelope helper (`main.emit`,
CONTRACTS.md §1) and posts a lifecycle line to the otto-ops Band feed
(phase-2 Task F hook), mirrored as a `band_msg` event.

Phase 3-A: every plan subtask (1-3) runs CONCURRENTLY (asyncio.gather) — the
never-cut fan-out visual (README-master-plan.md). Telemetry ticks every ~5s
with a placeholder cost — real cost lands Phase 4 via Respan.

Failure policy (architecture D7): `run_pipeline` NEVER raises and never
dies silently. The planner's Clarification comes back as an honest
`partial` result; any unexpected exception becomes an honest `failed`
result payload — the UI and `GET /status/:id` always get a well-formed
answer.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

from adapters.band import BandAdapter
from adapters.kimi import KimiAdapter
from adapters.mem0 import Mem0Adapter
from adapters.minimax import MinimaxAdapter
from adapters.retriever import RetrieverAdapter
from schemas import Clarification, Plan

#: The envelope emitter — `main.emit(type, payload)` (CONTRACTS.md §1).
Emit = Callable[[str, dict], Awaitable[None]]

#: band_msg short actor -> Band room long actor. CONTRACTS.md §5 rooms use
#: `planner | webagent-1.. | synthesizer`; the §1 `band_msg` mirror shortens
#: them to `plan | ag01.. | synth`.
_ROOM_ACTOR: Dict[str, str] = {
    "plan": "planner",
    "ag01": "webagent-1",
    "ag02": "webagent-2",
    "ag03": "webagent-3",
    "synth": "synthesizer",
}

#: Telemetry cadence (CONTRACTS.md §1 telemetry: "every ~5s").
_TELEMETRY_PERIOD_S = 5.0


async def _band(band: BandAdapter, emit: Emit, actor: str, text: str) -> None:
    """Post one lifecycle line to the otto-ops feed, THEN mirror it into the
    UI feed rail as a `band_msg` event (phase-2 Task F; CONTRACTS.md §1/§5).

    `actor` is the short UI form (`plan`/`ag01`/`synth`); the room post gets
    the long §5 identity. A feed hiccup never stalls the spine (D7).
    """
    try:
        await band.post(actor=_ROOM_ACTOR.get(actor, actor), text=text)
    except Exception:
        pass  # audit trail is best-effort; the spine must keep moving (D7)
    await emit("band_msg", {"actor": actor, "text": text})


def _fallback_result(
    request_id: str, status: str, spoken: str, elapsed_s: float
) -> Dict[str, Any]:
    """A well-formed §1 `result` payload with an empty card — used for the
    Clarification path and the D7 crash net. Validates as
    schemas.ResultPayload."""
    return {
        "request_id": request_id,
        "status": status,
        "spoken": spoken,
        "card": {"columns": [], "rows": []},
        "sources": [],
        "elapsed_s": elapsed_s,
        "cost_usd": 0.0,
        "agents": 0,
    }


async def run_pipeline(
    request_id: str, text: str, tasks: Dict[str, Dict[str, Any]], emit: Emit
) -> None:
    """Run one typed request through the whole spine (phase-2 Task D).

    Args:
        request_id: the `req_…` id `POST /task` answered with.
        text: the user's typed utterance.
        tasks: `main.TASKS` — updated in place to `done|failed` + result
            so `GET /status/:id` (CONTRACTS.md §6) always answers.
        emit: `main.emit` — wraps payloads in the §1 envelope.

    Never raises; never leaves `tasks[request_id]` stuck on "running" (D7).
    """
    t0 = time.monotonic()
    band = BandAdapter()
    entry = tasks.setdefault(
        request_id, {"text": text, "status": "running", "result": None}
    )
    ticker: Optional[asyncio.Task] = None

    try:
        # -- a. announce the run on the feed ---------------------------------
        await _band(band, emit, "plan", f"planning: {text[:60]}")

        # -- b. mem0 preference read (Phase 2 stub -> []) --------------------
        memory: List[str] = await Mem0Adapter().read(text)

        # -- c. plan | clarification (Kimi K3, phase-2 Task A) ---------------
        plan_or_q = await KimiAdapter().plan(text, memory, request_id)
        if isinstance(plan_or_q, Clarification):
            # Honesty path (D7): Otto asks aloud instead of guessing. The
            # question ships as a partial result with an empty card.
            payload = _fallback_result(
                request_id,
                status="partial",
                spoken=plan_or_q.question,
                elapsed_s=round(time.monotonic() - t0, 1),
            )
            await emit("result", payload)
            entry["status"] = "done"
            entry["result"] = payload
            await _band(band, emit, "plan", "clarification asked")
            return
        plan: Plan = plan_or_q

        # -- d. plan event (CONTRACTS.md §1 `plan`, exact field set) ---------
        await emit(
            "plan",
            {
                "request_id": plan.request_id or request_id,
                "spoken_ack": plan.spoken_ack,
                "recall": plan.recall,
                "subtasks": [
                    {
                        "id": st.id,
                        "target": st.target,
                        "title": st.title,
                        "steps_total": st.steps_total,
                    }
                    for st in plan.subtasks
                ],
            },
        )
        await _band(band, emit, "plan", f"plan ok · {len(plan.subtasks)} subtasks")

        # -- e. FAN-OUT: every subtask, concurrently (Phase 3-A) -------------
        # subtask index -> short actor id, ag01/ag02/ag03 (zero-padded, 1-based)
        actor_ids = [f"ag{i:02d}" for i in range(1, len(plan.subtasks) + 1)]
        for actor, subtask in zip(actor_ids, plan.subtasks):
            await _band(band, emit, actor, f"dispatch {actor} → {subtask.target}")

        async def _telemetry_ticker() -> None:
            """Emit §1 `telemetry` every ~5s until the run ends.

            cost_usd is a monotonic placeholder — real cost lands Ph4 via
            Respan.
            """
            while True:
                await asyncio.sleep(_TELEMETRY_PERIOD_S)
                elapsed = time.monotonic() - t0
                await emit(
                    "telemetry",
                    {
                        "cost_usd": round(0.01 + 0.002 * elapsed, 3),
                        "elapsed_s": int(elapsed),
                        "agents": len(plan.subtasks),
                        "gateway": "respan",
                    },
                )

        ticker = asyncio.create_task(_telemetry_ticker())

        def _make_on_step(subtask_id: str) -> Callable[[int, str, float], Awaitable[None]]:
            """Bind subtask_id by value (not closure-over-loop-var) so each
            agent's progress lands on ITS OWN pane, never the last one's."""

            async def on_step(step: int, line: str, elapsed_s: float) -> None:
                await emit(
                    "agent_update",
                    {
                        "subtask_id": subtask_id,
                        "status": "working",
                        "step": step,
                        "steps_total": next(
                            st.steps_total
                            for st in plan.subtasks
                            if st.id == subtask_id
                        ),
                        "line": line,
                        "elapsed_s": elapsed_s,
                    },
                )

            return on_step

        async def _run_one(actor: str, subtask) -> Any:
            """Run one subtask; an unexpected exception here becomes a
            well-formed failed AgentResult, never a crashed sibling (D7) —
            asyncio.gather(..., return_exceptions=False) is safe BECAUSE this
            function itself never raises."""
            from schemas import AgentResult  # local import avoids a cycle

            try:
                return await RetrieverAdapter().run_subtask(
                    subtask, _make_on_step(subtask.id)
                )
            except Exception as exc:  # pragma: no cover - defensive, D7
                return AgentResult(
                    subtask_id=subtask.id,
                    status="failed",
                    data={},
                    screenshot_ref=None,
                    steps_log=[f"unexpected error: {type(exc).__name__}: {exc}"],
                    elapsed_s=round(time.monotonic() - t0, 1),
                )

        results = await asyncio.gather(
            *(
                _run_one(actor, subtask)
                for actor, subtask in zip(actor_ids, plan.subtasks)
            )
        )

        # Final agent_update per agent: "ok" -> done, anything else -> failed
        # (§1 agent_update status has no "partial"). Then the screenshot
        # fallback visual + a band line, each addressed by its OWN actor id.
        for actor, subtask, result in zip(actor_ids, plan.subtasks, results):
            roles = result.data.get("roles")
            if not isinstance(roles, list):
                roles = None
            if roles is not None:
                newgrad = sum(
                    1
                    for r in roles
                    if isinstance(r, dict) and r.get("fit") == "new-grad"
                )
                line = f"{len(roles)} roles extracted · {result.elapsed_s}s"
            else:
                newgrad = 0
                line = f"no data extracted · {result.elapsed_s}s"
            final_update: Dict[str, Any] = {
                "subtask_id": subtask.id,
                "status": "done" if result.status == "ok" else "failed",
                "step": subtask.steps_total,
                "steps_total": subtask.steps_total,
                "line": line,
                "elapsed_s": result.elapsed_s,
            }
            if roles is not None and result.status == "ok":
                # summary_lines only on a "done" agent (CONTRACTS.md §1).
                final_update["summary_lines"] = {
                    "roles": len(roles),
                    "newgrad": newgrad,
                    "note": f"{newgrad} flagged new-grad friendly",
                }
            await emit("agent_update", final_update)

            # Screenshot fallback visual (§1 agent_screenshot) — live
            # retriever collects a ref on timeout/partial.
            if result.screenshot_ref:
                await emit(
                    "agent_screenshot",
                    {"subtask_id": subtask.id, "ref": result.screenshot_ref},
                )
            await _band(band, emit, actor, f"{result.status} · {result.elapsed_s}s")

        # -- f. synthesize (MiniMax M3, phase-2 Task C) ----------------------
        # Every DISPATCHED subtask is passed now — all of them were, so the
        # Phase-2 "only tell it about what ran" trim is a no-op here, kept
        # for symmetry with a future partial-dispatch scenario.
        await _band(band, emit, "synth", "synthesizing → minimax-m3")
        final = await MinimaxAdapter().synthesize(
            request_id,
            text,
            plan,
            list(results),
            elapsed_s=round(time.monotonic() - t0, 1),
        )

        # -- g. result event + store (CONTRACTS.md §1 `result` / §6) ---------
        final_dict = final.model_dump()
        await emit("result", final_dict)
        entry["status"] = "done"
        entry["result"] = final_dict
        await _band(
            band, emit, "synth", f"spoke · ${final.cost_usd:.2f} · {final.elapsed_s}s"
        )

    except Exception as exc:
        # -- h. D7 crash net: honest failed result, never a silent death -----
        payload = _fallback_result(
            request_id,
            status="failed",
            spoken="Something broke mid-run — nothing extracted, want me to retry?",
            elapsed_s=round(time.monotonic() - t0, 1),
        )
        entry["status"] = "failed"
        entry["result"] = payload
        try:
            await emit("result", payload)
            await _band(
                band, emit, "plan", f"error: {type(exc).__name__}: {exc}"[:160]
            )
        except Exception:
            pass  # even a broken emitter must not raise out of the pipeline
    finally:
        if ticker is not None:
            ticker.cancel()
            try:
                await ticker
            except (asyncio.CancelledError, Exception):
                pass
