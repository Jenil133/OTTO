"""OTTO — pydantic schemas for the pipeline (Phase 2 · Task A/D).

Field names mirror docs/CONTRACTS.md exactly — that file wins on conflicts.
These models are the *internal* spine contracts:

    planner  -> Plan | Clarification
    retriever adapter -> AgentResult          (CONTRACTS.md §3)
    synthesizer -> result payload dict        (CONTRACTS.md §1 `result`)

Validation rule (phase-2.md Task A): malformed plan JSON NEVER crashes the
pipeline — the orchestrator catches ValidationError and speaks a clarifying
question instead (architecture D7).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

#: docs/ALLOWLIST.md — the Zone-1 target list (architecture D5). Targets must
#: come from here (CONTRACTS.md §2, phase-2 Task B). Resolved from this file so
#: it works regardless of the process CWD.
ALLOWLIST_PATH = Path(__file__).resolve().parent.parent / "docs" / "ALLOWLIST.md"

#: Seed fallback if the file is unreadable — mirrors its first rows. Never crash.
_FALLBACK_ALLOWLIST = (
    "stripe.com/jobs",
    "anthropic.com/careers",
    "databricks.com/careers",
)


def load_allowlist_targets() -> List[str]:
    """Parse the `target` column from docs/ALLOWLIST.md (CONTRACTS.md §2:
    every Plan target must appear there). Unreadable file -> seed fallback."""
    targets: List[str] = []
    try:
        for raw in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line.startswith("|") or "---" in line:
                continue
            cell = line.strip("|").split("|")[0].strip()
            if cell and cell.lower() != "target":
                targets.append(cell)
    except OSError:
        pass
    return targets or list(_FALLBACK_ALLOWLIST)


class PlanSubtask(BaseModel):
    """One agent's read-only assignment (CONTRACTS.md §1 `plan.subtasks[]`)."""

    id: str
    target: str                       # allowlisted host/path, e.g. "stripe.com/jobs"
    title: str                        # doubles as the success criteria summary
    steps_total: int = 6
    instruction: str = ""             # natural-language instruction for Retriever
    success_criteria: str = ""
    output_schema: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("target")
    @classmethod
    def on_allowlist(cls, v: str) -> str:
        """Zone-1 gate (architecture D5 / CONTRACTS §2): reject any target not
        on docs/ALLOWLIST.md so a hallucinated live target triggers the D7
        Clarification path instead of driving a browser off-list."""
        if v.strip() not in load_allowlist_targets():
            raise ValueError(f"target '{v}' is not on the allowlist (docs/ALLOWLIST.md)")
        return v


class Plan(BaseModel):
    """Planner output (CONTRACTS.md §1 `plan` payload / §2).

    Hard rules encoded here, not just in the prompt: ≤3 subtasks, at least 1.
    """

    request_id: str = ""
    spoken_ack: str
    recall: List[str] = Field(default_factory=list)
    subtasks: List[PlanSubtask]

    @field_validator("subtasks")
    @classmethod
    def max_three(cls, v: List[PlanSubtask]) -> List[PlanSubtask]:
        if not 1 <= len(v) <= 3:
            raise ValueError("plan must have 1-3 subtasks")
        return v


class Clarification(BaseModel):
    """Planner's honest 'I need more info' path (phase-2.md Task A).

    The orchestrator turns this into a spoken question — never a crash (D7).
    """

    clarification_needed: Literal[True] = True
    question: str


class AgentResult(BaseModel):
    """Retriever adapter output (CONTRACTS.md §3). Timeout/failed still
    returns a WELL-FORMED instance with status partial|failed."""

    subtask_id: str
    status: Literal["ok", "partial", "failed"]
    data: Dict[str, Any] = Field(default_factory=dict)
    screenshot_ref: Optional[str] = None
    steps_log: List[str] = Field(default_factory=list)
    elapsed_s: float = 0.0


class ResultCard(BaseModel):
    """`result.card` (CONTRACTS.md §1)."""

    columns: List[str]
    rows: List[Dict[str, Any]]


class ResultPayload(BaseModel):
    """Synthesizer output == the §1 `result` event payload, verbatim."""

    request_id: str
    status: Literal["ok", "partial", "failed"]
    spoken: str
    card: ResultCard
    sources: List[str] = Field(default_factory=list)
    elapsed_s: float = 0.0
    cost_usd: float = 0.0
    agents: int = 1
