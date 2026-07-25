"""Tests for MinimaxAdapter.synthesize — phase-2 Task C, MOCK MODE ONLY.

No keys, no network: every test forces OTTO_MOCK=1 and strips
MINIMAX_API_KEY, so `synthesize()` exercises the pure-code composition path
(the same code that backs the D7 live-failure fallback). Assertions pin the
frozen shapes of docs/CONTRACTS.md §1 `result` via schemas.ResultPayload.

Run:  cd backend && .venv/bin/python -m pytest tests/test_synthesizer.py -q
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from adapters.minimax import MinimaxAdapter
from schemas import AgentResult, Plan, PlanSubtask, ResultPayload

# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def force_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guarantee mock mode (D6): no key + global kill-switch on."""
    monkeypatch.setenv("OTTO_MOCK", "1")
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)


STRIPE_ROLES: List[Dict[str, Any]] = [
    {
        "company": "Stripe",
        "role": "SWE, new grad",
        "location": "SF",
        "fit": "new-grad",
        "url": "https://stripe.com/jobs",
    },
    {
        "company": "Stripe",
        "role": "Backend Engineer, Payments",
        "location": "Remote (US)",
        "fit": "early-career",
        "url": "https://stripe.com/jobs",
    },
]

ANTHROPIC_ROLES: List[Dict[str, Any]] = [
    {
        "company": "Anthropic",
        "role": "Software Engineer, Early Career",
        "location": "SF",
        "fit": "new-grad",
        "url": "https://anthropic.com/careers",
    },
]


def make_plan() -> Plan:
    """Two-subtask jobs plan (CONTRACTS.md §2 shape)."""
    return Plan(
        request_id="req_test",
        spoken_ack="On it — two agents out.",
        subtasks=[
            PlanSubtask(id="st_1", target="stripe.com/jobs", title="Stripe new-grad SWE roles"),
            PlanSubtask(
                id="st_2", target="anthropic.com/careers", title="Anthropic early-career roles"
            ),
        ],
    )


def ok_result(subtask_id: str, roles: List[Dict[str, Any]]) -> AgentResult:
    return AgentResult(
        subtask_id=subtask_id,
        status="ok",
        data={"roles": roles},
        steps_log=["opened page", f"extracted {len(roles)} roles"],
        elapsed_s=40.0,
    )


def failed_result(subtask_id: str) -> AgentResult:
    return AgentResult(
        subtask_id=subtask_id,
        status="failed",
        data={},
        steps_log=["opened page", "bot wall — gave up"],
        elapsed_s=60.0,
    )


# ---------------------------------------------------------------------------
# Mock-path tests (phase-2 Task C test spec)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_ok_two_results() -> None:
    """All-ok: rows flattened across results, spoken mentions counts,
    sources are both plan targets, and the payload IS a ResultPayload."""
    adapter = MinimaxAdapter()
    plan = make_plan()
    results = [ok_result("st_1", STRIPE_ROLES), ok_result("st_2", ANTHROPIC_ROLES)]

    out = await adapter.synthesize(
        request_id="req_test",
        user_text="find new-grad SDE roles",
        plan=plan,
        results=results,
        elapsed_s=42.0,
    )

    assert isinstance(out, ResultPayload)
    assert out.status == "ok"
    assert out.request_id == "req_test"
    # Rows = flatten of both results' data["roles"], nothing added.
    assert out.card.rows == STRIPE_ROLES + ANTHROPIC_ROLES
    assert out.card.columns == ["company", "role", "location", "fit"]
    # Spoken mentions the counts: 3 roles, 2 sites, 2 new-grad friendly.
    assert "Found 3 roles" in out.spoken
    assert "2 sites" in out.spoken
    assert "2 look new-grad friendly" in out.spoken
    assert "Want the links?" in out.spoken
    # Sources = plan targets of the non-failed results.
    assert out.sources == ["stripe.com/jobs", "anthropic.com/careers"]
    assert out.agents == 2
    assert out.elapsed_s == 42.0
    assert out.cost_usd == 0.0
    # Round-trips through the frozen schema (CONTRACTS.md §1 `result`).
    ResultPayload.model_validate(out.model_dump())


@pytest.mark.asyncio
async def test_one_failed_is_partial_and_admits_it() -> None:
    """One failure: status partial, spoken SAYS a site did not finish,
    failed target excluded from sources, only real rows kept."""
    adapter = MinimaxAdapter()
    plan = make_plan()
    results = [ok_result("st_1", STRIPE_ROLES), failed_result("st_2")]

    out = await adapter.synthesize(
        request_id="req_test",
        user_text="find new-grad SDE roles",
        plan=plan,
        results=results,
        elapsed_s=61.0,
    )

    assert out.status == "partial"
    assert "One site did not finish" in out.spoken  # honesty path (D7)
    assert out.card.rows == STRIPE_ROLES
    assert out.sources == ["stripe.com/jobs"]  # failed target is NOT a source
    assert out.agents == 2
    ResultPayload.model_validate(out.model_dump())


@pytest.mark.asyncio
async def test_all_failed_is_honest() -> None:
    """All failed: status failed, empty rows, honest spoken with no invented
    counts, and zero fabricated sources."""
    adapter = MinimaxAdapter()
    plan = make_plan()
    results = [failed_result("st_1"), failed_result("st_2")]

    out = await adapter.synthesize(
        request_id="req_test",
        user_text="find new-grad SDE roles",
        plan=plan,
        results=results,
        elapsed_s=60.0,
    )

    assert out.status == "failed"
    assert out.card.rows == []
    assert out.sources == []  # nothing reached -> nothing fabricated
    assert "could not get into" in out.spoken.lower()
    assert "nothing extracted" in out.spoken.lower()
    assert "retry" in out.spoken.lower()
    assert "Found" not in out.spoken  # no invented result counts
    ResultPayload.model_validate(out.model_dump())


@pytest.mark.asyncio
async def test_partial_status_result_counts_as_reached() -> None:
    """An agent-level `partial` result: overall status partial, its target
    still counts as a reached source, its rows are used."""
    adapter = MinimaxAdapter()
    plan = make_plan()
    partial = AgentResult(
        subtask_id="st_2",
        status="partial",
        data={"roles": ANTHROPIC_ROLES},
        steps_log=["opened page", "timed out mid-extract"],
        elapsed_s=60.0,
    )
    out = await adapter.synthesize(
        request_id="req_test",
        user_text="find new-grad SDE roles",
        plan=plan,
        results=[ok_result("st_1", STRIPE_ROLES), partial],
        elapsed_s=63.0,
    )

    assert out.status == "partial"
    assert out.card.rows == STRIPE_ROLES + ANTHROPIC_ROLES
    assert out.sources == ["stripe.com/jobs", "anthropic.com/careers"]


def test_screenshot_recovery_stub_appends_image_block() -> None:
    """Screenshot-recovery STUB (phase-2 Task C): empty data + screenshot_ref
    -> the built user message grows a multimodal image content block.
    (UNTESTED against the live API — format awaits VERIFY.md.)"""
    adapter = MinimaxAdapter()
    plan = make_plan()
    shot = AgentResult(
        subtask_id="st_2",
        status="partial",
        data={},
        screenshot_ref="https://shots.example/st_2.png",
        steps_log=["opened page"],
        elapsed_s=58.0,
    )
    content = adapter._build_user_content(
        "find new-grad SDE roles", plan, [ok_result("st_1", STRIPE_ROLES), shot]
    )

    assert isinstance(content, list)  # text block + image block(s)
    assert content[0]["type"] == "text"
    image_blocks = [b for b in content[1:] if b.get("type") == "image_url"]
    assert image_blocks == [
        {"type": "image_url", "image_url": {"url": "https://shots.example/st_2.png"}}
    ]

    # No empty-data screenshots -> plain string user message.
    plain = adapter._build_user_content(
        "find new-grad SDE roles", plan, [ok_result("st_1", STRIPE_ROLES)]
    )
    assert isinstance(plain, str)


def test_legacy_call_mock_still_works() -> None:
    """Backwards compat: Phase 1 `call()` path returns the canned §1 `result`
    dict and it still validates against the frozen schema."""
    out = MinimaxAdapter().call(request_id="req_legacy")
    assert isinstance(out, dict)
    assert out["request_id"] == "req_legacy"
    ResultPayload.model_validate(out)
