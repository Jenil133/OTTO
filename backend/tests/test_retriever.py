"""Tests for the Retriever adapter (Phase 2 · Task B, code half).

All tests run in MOCK mode: no keys, no network, mock_step_delay=0.
Run:  cd backend && .venv/bin/python -m pytest tests/test_retriever.py -q
"""

from __future__ import annotations

from typing import List, Tuple

import pytest

from adapters.retriever import RetrieverAdapter
from schemas import AgentResult, PlanSubtask


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guarantee mock mode: no Retriever key, no global force flag leaking in."""
    monkeypatch.delenv("RETRIEVER_API_KEY", raising=False)
    monkeypatch.delenv("OTTO_MOCK", raising=False)


def make_subtask(target: str = "stripe.com/jobs", sid: str = "st_1") -> PlanSubtask:
    """A minimal valid PlanSubtask (CONTRACTS.md §1 plan.subtasks[])."""
    return PlanSubtask(
        id=sid,
        target=target,
        title=f"new-grad roles on {target}",
        instruction="Extract new-grad software roles",
        output_schema={"roles": []},
    )


@pytest.mark.asyncio
async def test_mock_returns_ok_agent_result_with_roles_and_six_steps() -> None:
    adapter = RetrieverAdapter(mock_step_delay=0)
    result = await adapter.run_subtask(make_subtask())

    assert isinstance(result, AgentResult)
    assert result.subtask_id == "st_1"
    assert result.status == "ok"
    assert len(result.steps_log) == 6
    assert result.elapsed_s > 0

    roles = result.data["roles"]
    assert len(roles) == 3  # canned Stripe flavor per phase-2 Task B
    for row in roles:  # CONTRACTS.md §3 data shape
        assert set(row) == {"company", "role", "location", "fit", "url"}
        assert row["company"] == "Stripe"


@pytest.mark.asyncio
async def test_on_step_fires_six_times_with_increasing_steps() -> None:
    adapter = RetrieverAdapter(mock_step_delay=0)
    calls: List[Tuple[int, str, float]] = []

    async def on_step(step: int, line: str, elapsed_s: float) -> None:
        calls.append((step, line, elapsed_s))

    result = await adapter.run_subtask(make_subtask(), on_step=on_step)

    assert [c[0] for c in calls] == [1, 2, 3, 4, 5, 6]
    assert [c[1] for c in calls] == result.steps_log
    elapsed = [c[2] for c in calls]
    assert elapsed == sorted(elapsed)  # non-decreasing
    for e in elapsed:
        assert round(e, 1) == e  # truncated to 1 decimal
    assert calls[0][1].startswith("opening stripe.com/jobs")


@pytest.mark.asyncio
async def test_anthropic_flavor_returns_five_roles_two_newgrad() -> None:
    adapter = RetrieverAdapter(mock_step_delay=0)
    result = await adapter.run_subtask(
        make_subtask(target="anthropic.com/careers", sid="st_2")
    )

    roles = result.data["roles"]
    assert len(roles) == 5  # mockRun.js st_2: roles 5
    assert sum(1 for r in roles if r["fit"] == "new-grad") == 2  # newgrad 2
    assert result.steps_log[0] == "opening anthropic.com/careers"
    assert "5 roles matched" in result.steps_log[4]


@pytest.mark.asyncio
async def test_databricks_flavor_returns_one_to_three_roles() -> None:
    adapter = RetrieverAdapter(mock_step_delay=0)
    result = await adapter.run_subtask(
        make_subtask(target="databricks.com/careers", sid="st_3")
    )

    roles = result.data["roles"]
    assert 1 <= len(roles) <= 3
    assert sum(1 for r in roles if r["fit"] == "new-grad") >= 1
    assert all(r["company"] == "Databricks" for r in roles)


@pytest.mark.asyncio
async def test_generic_flavor_extracts_two_roles_on_target() -> None:
    adapter = RetrieverAdapter(mock_step_delay=0)
    result = await adapter.run_subtask(make_subtask(target="figma.com/careers"))

    roles = result.data["roles"]
    assert len(roles) == 2
    assert all("figma.com" in r["url"] for r in roles)
    assert all(r["company"] == "Figma" for r in roles)


@pytest.mark.asyncio
async def test_on_step_none_is_fine() -> None:
    adapter = RetrieverAdapter(mock_step_delay=0)
    result = await adapter.run_subtask(make_subtask(), on_step=None)
    assert result.status == "ok"
    assert len(result.steps_log) == 6


@pytest.mark.asyncio
async def test_result_validates_as_agent_result_schema() -> None:
    adapter = RetrieverAdapter(mock_step_delay=0)
    result = await adapter.run_subtask(make_subtask())
    # Round-trips through the frozen schema (CONTRACTS.md §3).
    revalidated = AgentResult.model_validate(result.model_dump())
    assert revalidated == result


@pytest.mark.asyncio
async def test_otto_mock_forces_mock_even_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D6 kill-switch: OTTO_MOCK=1 + key present must NOT hit the network."""
    monkeypatch.setenv("RETRIEVER_API_KEY", "fake-key")
    monkeypatch.setenv("OTTO_MOCK", "1")
    adapter = RetrieverAdapter(mock_step_delay=0)
    result = await adapter.run_subtask(make_subtask())
    assert result.status == "ok"
    assert result.data["roles"]


def test_legacy_call_returns_contracts_dict() -> None:
    """Backwards compat: sync BaseAdapter.call() still serves the §3 dict."""
    adapter = RetrieverAdapter()
    out = adapter.call(subtask_id="st_9")
    assert out["subtask_id"] == "st_9"
    assert out["status"] == "ok"
    assert set(out) == {
        "subtask_id", "status", "data", "screenshot_ref", "steps_log", "elapsed_s",
    }
    assert len(out["steps_log"]) == 6
    # Legacy dict itself validates against the frozen model.
    AgentResult.model_validate(out)
