"""Tests for the Kimi K3 planner adapter — phase-2 Task A, mock mode only.

Runs with NO keys and NO network (architecture D6): `OTTO_MOCK=1` is forced
per-test so `KimiAdapter.plan()` always takes the deterministic mock path.
Covers the three canned utterances required by phase-2 Task A (jobs /
shopping / ambiguous) plus the pydantic guard rails of CONTRACTS.md §2.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_planner.py -q
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from adapters.kimi import KimiAdapter, _load_allowlist_targets, _system_prompt
from schemas import Clarification, Plan, PlanSubtask

#: Seed rows of docs/ALLOWLIST.md (CONTRACTS.md §2: targets must come from it).
ALLOWLISTED = set(_load_allowlist_targets())


@pytest.fixture()
def adapter(monkeypatch: pytest.MonkeyPatch) -> KimiAdapter:
    """A KimiAdapter forced into mock mode — no key, global kill-switch on."""
    monkeypatch.delenv("TOKENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OTTO_MOCK", "1")
    a = KimiAdapter()
    assert not a.live  # sanity: nothing below may touch the network
    return a


# --------------------------------------------------------------------------- #
# Canned utterance 1 — jobs (phase-2 Task A unit-test requirement)            #
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_jobs_utterance_returns_allowlisted_plan(adapter: KimiAdapter) -> None:
    out = await adapter.plan(
        "find new-grad SDE roles at Stripe", ["new-grad", "bay area"], "req_j1"
    )
    assert isinstance(out, Plan)
    assert 1 <= len(out.subtasks) <= 3
    assert out.spoken_ack.strip()  # nonempty ack in Otto's voice
    for st in out.subtasks:
        assert st.target in ALLOWLISTED  # allowlist-only targets (§2)
        assert st.instruction.strip()  # explicit agent brief
        assert st.success_criteria.strip()  # explicit success criteria
        assert st.output_schema  # explicit output shape
    assert out.recall == ["new-grad", "bay area"]  # jobs-flavored recall echo


# --------------------------------------------------------------------------- #
# Canned utterance 2 — shopping                                               #
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_shopping_utterance_returns_plan(adapter: KimiAdapter) -> None:
    out = await adapter.plan(
        "find the cheapest RTX 4070 under $500", [], "req_s1"
    )
    assert isinstance(out, Plan)
    assert 1 <= len(out.subtasks) <= 3
    assert out.spoken_ack.strip()
    for st in out.subtasks:
        assert st.instruction.strip() and st.success_criteria.strip()
        assert st.output_schema


# --------------------------------------------------------------------------- #
# Canned utterance 3 — ambiguous -> clarify, never guess (D7)                 #
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_ambiguous_utterance_returns_clarification(adapter: KimiAdapter) -> None:
    out = await adapter.plan("help me with something good", [], "req_a1")
    assert isinstance(out, Clarification)
    assert out.clarification_needed is True
    assert out.question.strip()


# --------------------------------------------------------------------------- #
# Guard rails                                                                 #
# --------------------------------------------------------------------------- #


def test_plan_model_rejects_four_subtasks() -> None:
    """CONTRACTS.md §2 hard rule: <=3 subtasks, enforced by pydantic."""
    subtask = {
        "id": "st_1",
        "target": "stripe.com/jobs",
        "title": "t",
        "steps_total": 6,
    }
    with pytest.raises(ValidationError):
        Plan(
            spoken_ack="too many",
            subtasks=[
                {**subtask, "id": f"st_{i}"} for i in range(1, 5)
            ],
        )


@pytest.mark.asyncio
async def test_plan_sets_request_id(adapter: KimiAdapter) -> None:
    out = await adapter.plan("find new-grad SDE roles at Stripe", [], "req_42")
    assert isinstance(out, Plan)
    assert out.request_id == "req_42"


@pytest.mark.asyncio
async def test_default_plan_matches_golden_run(adapter: KimiAdapter) -> None:
    """No company / no shopping words -> the canonical mockRun.js job plan."""
    out = await adapter.plan(
        "find new grad software engineering jobs in the bay area", [], "req_g1"
    )
    assert isinstance(out, Plan)
    assert [st.target for st in out.subtasks] == [
        "stripe.com/jobs",
        "anthropic.com/careers",
        "databricks.com/careers",
    ]
    assert all(st.steps_total == 6 for st in out.subtasks)
    assert all(isinstance(st, PlanSubtask) for st in out.subtasks)


def test_legacy_call_still_returns_canned_plan_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase-1 sync `call()` path stays working (D6 backwards compat)."""
    monkeypatch.setenv("OTTO_MOCK", "1")
    out = KimiAdapter().call(request_id="req_legacy")
    assert out["request_id"] == "req_legacy"
    assert len(out["subtasks"]) == 3


def test_system_prompt_substitutes_allowlist() -> None:
    """{{ALLOWLIST}} placeholder is replaced with real targets (Task A)."""
    prompt = _system_prompt()
    assert "{{ALLOWLIST}}" not in prompt
    for target in ALLOWLISTED:
        assert target in prompt
