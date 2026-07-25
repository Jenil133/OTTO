"""Tests for the orchestrator spine (Phase 2 · Task D + Task F fallback feed).

All tests run in MOCK mode: no keys, no network, retriever step delay 0.
`run_pipeline` is awaited directly with a collected list standing in for
`main.emit` and a plain dict standing in for `main.TASKS`.

Run:  cd backend && .venv/bin/python -m pytest tests/test_pipeline.py -q
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

import pipeline
from adapters import band as band_module
from adapters.retriever import RetrieverAdapter
from schemas import ResultPayload

#: Every sponsor key the spine's adapters look at, plus the global override.
_ENV_KEYS = (
    "OTTO_MOCK",
    "TOKENROUTER_API_KEY",
    "RETRIEVER_API_KEY",
    "MINIMAX_API_KEY",
    "MEM0_API_KEY",
    "BAND_API_KEY",
    "BAND_ROOM",
)


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch):
    """Guarantee mock mode (D6) + instant retriever + a clean Band feed.

    The retriever mock exposes its pacing as the `mock_step_delay`
    constructor arg (tests pass 0 per its own docstring); the pipeline
    instantiates `pipeline.RetrieverAdapter()` at call time, so patching the
    module attribute swaps in a zero-delay factory.
    """
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(
        pipeline, "RetrieverAdapter", lambda: RetrieverAdapter(mock_step_delay=0)
    )
    band_module.FEED.clear()
    yield
    band_module.FEED.clear()


class Collector:
    """Fake `main.emit` — records (type, payload) tuples in order."""

    def __init__(self) -> None:
        self.events: List[Tuple[str, dict]] = []

    async def __call__(self, type: str, payload: dict) -> None:
        self.events.append((type, payload))

    @property
    def types(self) -> List[str]:
        return [t for t, _ in self.events]

    def of(self, event_type: str) -> List[dict]:
        return [p for t, p in self.events if t == event_type]


# ---------------------------------------------------------------------------
# Happy path — plan → ≥3 working agent_updates → done → result (Task D)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_event_sequence() -> None:
    emit = Collector()
    tasks: Dict[str, Any] = {}
    await pipeline.run_pipeline(
        "req_t1", "find new-grad SDE roles at stripe", tasks, emit
    )

    types = emit.types
    assert "plan" in types and "result" in types and "agent_update" in types
    # Ordering per CONTRACTS.md §1 flow: plan before the first agent_update
    # before the final result.
    assert types.index("plan") < types.index("agent_update") < types.index("result")

    working = [p for p in emit.of("agent_update") if p["status"] == "working"]
    done = [p for p in emit.of("agent_update") if p["status"] == "done"]
    assert len(working) >= 3  # retriever mock streams 6 canned steps
    assert len(done) == 1

    final = done[0]
    assert final["step"] == final["steps_total"]
    # summary_lines only on done, with the frozen keys (CONTRACTS.md §1).
    assert set(final["summary_lines"]) == {"roles", "newgrad", "note"}
    assert "roles extracted" in final["line"]


@pytest.mark.asyncio
async def test_happy_path_plan_payload_matches_contracts_section_1() -> None:
    emit = Collector()
    await pipeline.run_pipeline(
        "req_t2", "find new-grad SDE roles at stripe", {}, emit
    )

    plans = emit.of("plan")
    assert len(plans) == 1
    plan = plans[0]
    assert plan["request_id"] == "req_t2"
    assert set(plan) == {"request_id", "spoken_ack", "recall", "subtasks"}
    for st in plan["subtasks"]:
        # Exactly the §1 subtask field set — planner internals trimmed.
        assert set(st) == {"id", "target", "title", "steps_total"}


@pytest.mark.asyncio
async def test_happy_path_stores_done_result_that_validates() -> None:
    emit = Collector()
    tasks: Dict[str, Any] = {}
    await pipeline.run_pipeline(
        "req_t3", "find new-grad SDE roles at stripe", tasks, emit
    )

    entry = tasks["req_t3"]
    assert entry["status"] == "done"
    validated = ResultPayload.model_validate(entry["result"])  # §1 `result`
    assert validated.status == "ok"
    assert validated.request_id == "req_t3"
    assert validated.card.rows  # canned Stripe roles made it through
    # The stored result is byte-identical to the emitted `result` event.
    assert emit.of("result")[-1] == entry["result"]


# ---------------------------------------------------------------------------
# Band feed — Task F fallback + band_msg mirror
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_band_msgs_mirrored_and_internal_feed_populated() -> None:
    emit = Collector()
    await pipeline.run_pipeline(
        "req_t4", "find new-grad SDE roles at stripe", {}, emit
    )

    band_events = emit.of("band_msg")
    assert band_events  # lifecycle lines flowed
    assert all(set(p) == {"actor", "text"} for p in band_events)  # §1 band_msg
    # Short UI actors on the mirror (CONTRACTS.md §1)…
    actors = {p["actor"] for p in band_events}
    assert {"plan", "ag01", "synth"} <= actors

    # …and one §5-shaped room message per mirrored line in the internal
    # fallback feed (phase-2 Task F).
    assert len(band_module.FEED) == len(band_events)
    for msg in band_module.FEED:
        assert set(msg) == {"room", "actor", "text", "ts"}
        assert msg["room"] == "otto-ops"
    room_actors = {m["actor"] for m in band_module.FEED}
    assert {"planner", "webagent-1", "synthesizer"} <= room_actors


# ---------------------------------------------------------------------------
# Clarification path — honest partial result, NO plan event (Task A/D honesty)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clarification_path_partial_result_and_no_plan_event() -> None:
    emit = Collector()
    tasks: Dict[str, Any] = {}
    await pipeline.run_pipeline("req_t5", "help me", tasks, emit)

    # Otto asks aloud instead of guessing: no plan, no agents dispatched.
    assert "plan" not in emit.types
    assert "agent_update" not in emit.types

    results = emit.of("result")
    assert len(results) == 1
    payload = results[0]
    assert payload["status"] == "partial"
    assert "?" in payload["spoken"]  # it's an actual question
    assert payload["card"] == {"columns": [], "rows": []}
    assert payload["agents"] == 0
    ResultPayload.model_validate(payload)  # still a well-formed §1 result

    assert tasks["req_t5"]["status"] == "done"
    assert tasks["req_t5"]["result"] == payload


# ---------------------------------------------------------------------------
# D7 crash net — unexpected exception → honest failed result, never silent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unexpected_crash_yields_honest_failed_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BoomPlanner:
        async def plan(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("boom")  # simulate any unexpected stage bug

    monkeypatch.setattr(pipeline, "KimiAdapter", lambda: BoomPlanner())

    emit = Collector()
    tasks: Dict[str, Any] = {}
    await pipeline.run_pipeline("req_t6", "find roles at stripe", tasks, emit)

    results = emit.of("result")
    assert len(results) == 1
    payload = results[0]
    assert payload["status"] == "failed"
    assert "retry" in payload["spoken"]
    ResultPayload.model_validate(payload)  # well-formed even on crash (D7)

    assert tasks["req_t6"]["status"] == "failed"
    assert tasks["req_t6"]["result"] == payload
    # The error also hit the feed rail — nothing dies silently.
    assert any("error" in p["text"] for p in emit.of("band_msg"))
