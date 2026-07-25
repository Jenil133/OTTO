"""Must-not suite — one test per FORBIDDEN outcome (PDD validation ladder L3).

Each test pins a "Must not" line from Otto's issue discipline: not what the
system does, but what it must NEVER do — off-allowlist targets, >3 subtasks,
fabricated rows, crashes on ambiguity, write-action agents, leaked keys,
silent pipeline death.

All tests run in MOCK mode: zero keys, zero network (D6). The autouse
fixture strips every sponsor key and forces `OTTO_MOCK=1`, same pattern as
tests/test_pipeline.py.

Run:  cd backend && .venv/bin/python -m pytest tests/test_mustnot.py -q
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from pydantic import ValidationError

import pipeline
from adapters import band as band_module
from adapters.kimi import KimiAdapter
from adapters.minimax import MinimaxAdapter
from adapters.retriever import RetrieverAdapter
from schemas import AgentResult, Clarification, Plan, PlanSubtask, ResultPayload

#: Every sponsor key an adapter looks at, plus the global mock override
#: (mirrors tests/test_pipeline.py so no live key can leak into a test).
_ENV_KEYS = (
    "OTTO_MOCK",
    "TOKENROUTER_API_KEY",
    "RETRIEVER_API_KEY",
    "MINIMAX_API_KEY",
    "MEM0_API_KEY",
    "BAND_API_KEY",
    "BAND_ROOM",
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

_PLANNER_PROMPT = _REPO_ROOT / "backend" / "prompts" / "planner.md"


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch):
    """Zero keys + global kill-switch on (D6): nothing below may touch the
    network. Retriever swaps to a zero-delay factory; Band feed starts clean."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OTTO_MOCK", "1")
    monkeypatch.setattr(
        pipeline, "RetrieverAdapter", lambda: RetrieverAdapter(mock_step_delay=0)
    )
    band_module.FEED.clear()
    yield
    band_module.FEED.clear()


class Collector:
    """Fake `main.emit` — records (type, payload) tuples in order
    (same shape as tests/test_pipeline.py)."""

    def __init__(self) -> None:
        self.events: List[Tuple[str, dict]] = []

    async def __call__(self, type: str, payload: dict) -> None:
        self.events.append((type, payload))

    @property
    def types(self) -> List[str]:
        return [t for t, _ in self.events]

    def of(self, event_type: str) -> List[dict]:
        return [p for t, p in self.events if t == event_type]


def _failed(subtask_id: str) -> AgentResult:
    return AgentResult(
        subtask_id=subtask_id,
        status="failed",
        data={},
        steps_log=["opened page", "bot wall — gave up"],
        elapsed_s=60.0,
    )


# ---------------------------------------------------------------------------
# Must not: drive a browser at any target off docs/ALLOWLIST.md (Zone-3, D5)
# ---------------------------------------------------------------------------


def test_mustnot_plan_off_allowlist() -> None:
    """linkedin.com/jobs is the canonical Zone-3 target (login wall). The
    pydantic gate `schemas.PlanSubtask.on_allowlist` must reject it at
    validation time — a hallucinated target never reaches a browser."""
    with pytest.raises(ValidationError, match="allowlist"):
        PlanSubtask(
            id="st_1",
            target="linkedin.com/jobs",
            title="new-grad roles on LinkedIn",
        )


# ---------------------------------------------------------------------------
# Must not: fan out more than 3 agents (CONTRACTS.md §2 hard rule)
# ---------------------------------------------------------------------------


def test_mustnot_more_than_three_subtasks() -> None:
    """4 subtasks — every target individually legal — must still fail the
    Plan-level `max_three` validator: the cap is enforced in code, not
    merely requested in the prompt."""
    legal_targets = [
        "stripe.com/jobs",
        "anthropic.com/careers",
        "databricks.com/careers",
        "figma.com/careers",
    ]
    with pytest.raises(ValidationError, match="1-3 subtasks"):
        Plan(
            spoken_ack="too many agents",
            subtasks=[
                PlanSubtask(id=f"st_{i}", target=t, title=f"roles on {t}")
                for i, t in enumerate(legal_targets, start=1)
            ],
        )


# ---------------------------------------------------------------------------
# Must not: fabricate rows or sources when every agent failed (D7 honesty)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mustnot_fabricate_rows_on_total_failure() -> None:
    """All agents failed -> the synthesizer's mock composition must return an
    EMPTY card and EMPTY sources: nothing reached, nothing invented."""
    plan = Plan(
        request_id="req_mn1",
        spoken_ack="On it.",
        subtasks=[
            PlanSubtask(id="st_1", target="stripe.com/jobs", title="Stripe roles"),
            PlanSubtask(id="st_2", target="anthropic.com/careers", title="Anthropic roles"),
        ],
    )
    out = await MinimaxAdapter().synthesize(
        request_id="req_mn1",
        user_text="find new-grad SDE roles",
        plan=plan,
        results=[_failed("st_1"), _failed("st_2")],
        elapsed_s=60.0,
    )
    assert isinstance(out, ResultPayload)
    assert out.status == "failed"
    assert out.card.rows == []      # zero fabricated rows
    assert out.sources == []        # zero fabricated sources
    assert "Found" not in out.spoken  # no invented counts in the spoken line


# ---------------------------------------------------------------------------
# Must not: crash (or guess a Plan) on an ambiguous ask (Task A honesty path)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mustnot_crash_on_ambiguous() -> None:
    """An ambiguous utterance must come back as a Clarification object —
    never an exception, never a guessed Plan."""
    out = await KimiAdapter().plan("help me with something good", [], "req_mn2")
    assert isinstance(out, Clarification)
    assert not isinstance(out, Plan)
    assert out.clarification_needed is True
    assert out.question.strip()


# ---------------------------------------------------------------------------
# Must not: ship a planner prompt without the read-only Zone-1 rules (D5)
# ---------------------------------------------------------------------------


def test_mustnot_writeaction_verbs_in_planner_prompt() -> None:
    """backend/prompts/planner.md is a judged PDD artifact: the hard safety
    section must state the read-only rule and explicitly forbid the write
    actions (purchase / log in / credentials / irreversible)."""
    text = _PLANNER_PROMPT.read_text(encoding="utf-8")
    lower = text.lower()
    assert "read-only actions only" in lower          # the Zone-1 rule
    assert "never" in lower                           # the forbidden list exists
    assert "purchase anything" in lower               # …and forbids purchases
    assert "log in" in lower                          # …and logins
    assert "enter credentials" in lower               # …and credentials
    assert "irreversible" in lower                    # …and irreversible acts


# ---------------------------------------------------------------------------
# Must not: leak the API key into any tracked file (PDD security rule)
# ---------------------------------------------------------------------------


def test_mustnot_secrets_in_tracked_files() -> None:
    """The real key lives ONLY in backend/.env (gitignored). Scan every
    tracked source/prompt/doc surface for the key prefix and demand zero
    hits. The needle is built by concatenation so this file never contains
    the contiguous prefix itself — and never the full key."""
    needle = "sk-" + "DY"  # 5-char prefix only; the full key appears nowhere
    # Repo-wide recursive scan (every tracked text surface, incl. root *.md,
    # completed/, tests themselves) minus generated/dependency/env dirs. A key
    # pasted into ANY doc — even PDD.md — must fail the suite (DoD #4).
    skip_parts = {".venv", "node_modules", "dist", ".git", "__pycache__"}
    skip_names = {".env", ".DS_Store"}  # .env legitimately holds the key
    exts = {".py", ".md", ".js", ".jsx", ".css", ".html", ".json", ".txt", ".example"}
    offenders: List[str] = []
    for path in sorted(_REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if skip_parts.intersection(path.parts) or path.name in skip_names:
            continue
        if path.suffix not in exts and path.name != ".env.example":
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if needle in content:
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert offenders == [], f"key prefix leaked into: {offenders}"


# ---------------------------------------------------------------------------
# Must not: die silently on an unexpected crash (D7 crash net)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mustnot_pipeline_die_silently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Planner explodes mid-run -> the pipeline must STILL emit a well-formed
    `result` event and mark the task failed. No exception escapes, no task
    stays stuck on 'running', the error hits the feed rail."""

    class BoomPlanner:
        async def plan(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("mustnot-boom")

    monkeypatch.setattr(pipeline, "KimiAdapter", lambda: BoomPlanner())

    emit = Collector()
    tasks: Dict[str, Any] = {}
    # If run_pipeline raised, this await would propagate and fail the test.
    await pipeline.run_pipeline("req_mn3", "find roles at stripe", tasks, emit)

    results = emit.of("result")
    assert len(results) == 1                          # it spoke, even broken
    payload = results[0]
    assert payload["status"] == "failed"
    ResultPayload.model_validate(payload)             # still a §1 result
    assert tasks["req_mn3"]["status"] == "failed"     # never stuck "running"
    assert tasks["req_mn3"]["result"] == payload
    assert any("error" in p["text"] for p in emit.of("band_msg"))
