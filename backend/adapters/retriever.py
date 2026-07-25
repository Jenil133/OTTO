"""Retriever adapter — cloud browser sessions (Zone-1 web, architecture D1/D5).

Phase 2 · Task B (code half). One `RetrieverAdapter.run_subtask()` call runs
ONE browser subtask against an allowlisted target and returns an
`AgentResult` (docs/CONTRACTS.md §3) — ALWAYS well-formed, even on timeout,
HTTP error, or garbage responses (architecture D7: never crash the pipeline).

Dispatch (D6): `run_subtask` checks `self.live` itself —
    live (key present, OTTO_MOCK unset) → submit-then-poll against the real
        Retriever API (routes are env-overridable; exact values land in
        VERIFY.md Saturday — every assumption below carries a `# VERIFY:`).
    mock → canned Stripe-jobs run (phase-2.md Task B: "Mock mode returns a
        canned Stripe-jobs result so P2 never waits on you"), flavored by
        `subtask.target` and paced by `mock_step_delay`.

The legacy sync `call()` / `_mock()` path of `BaseAdapter` is preserved for
backwards compat; new code goes through `run_subtask`.
"""

from __future__ import annotations

import asyncio
import math
import os
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx

from schemas import AgentResult, PlanSubtask

from .base import BaseAdapter

#: Async progress callback: on_step(step_1_based, line, elapsed_s).
#: The orchestrator turns these into `agent_update` events (CONTRACTS.md §1).
OnStep = Callable[[int, str, float], Awaitable[None]]

#: Hard wall-clock cap per subtask (phase-2.md Task B + architecture D2).
HARD_CAP_S = 60.0

#: Poll cadence against the Retriever session route (phase-2.md Task B).
POLL_INTERVAL_S = 2.0

# VERIFY: exact terminal status strings Sat (VERIFY.md) — superset guess.
_TERMINAL_OK = {"done", "complete", "completed", "succeeded", "ok"}
_TERMINAL_FAILED = {"failed", "error", "errored", "cancelled", "canceled"}


def _trunc1(x: float) -> float:
    """Truncate to 1 decimal place (phase-2 Task B: elapsed_s formatting)."""
    return math.floor(x * 10) / 10.0


# ---------------------------------------------------------------------------
# Canned mock flavors — numbers consistent with frontend/src/mockRun.js so the
# real-mock demo looks like the golden run (D4/D6).
# ---------------------------------------------------------------------------

#: Default canned run — Stripe jobs (mockRun.js st_1 beats; 3 rows per Task B).
_STRIPE = {
    "target": "stripe.com/jobs",
    "roles": [
        {"company": "Stripe", "role": "SWE, new grad", "location": "SF",
         "fit": "new-grad", "url": "https://stripe.com/jobs"},
        {"company": "Stripe", "role": "Infrastructure eng", "location": "SF",
         "fit": "mid", "url": "https://stripe.com/jobs"},
        {"company": "Stripe", "role": "Backend Engineer, Payments",
         "location": "Remote (US)", "fit": "early-career",
         "url": "https://stripe.com/jobs"},
    ],
    "step_elapsed": [1.0, 4.0, 9.0, 15.0, 19.0, 31.0],  # mockRun.js st_1
    "elapsed_s": 48.0,                                   # ag01 done · 48s
}

#: Anthropic flavor — 5 roles, 2 new-grad (mockRun.js st_2: roles 5, newgrad 2).
_ANTHROPIC = {
    "target": "anthropic.com/careers",
    "roles": [
        {"company": "Anthropic", "role": "SWE, early career", "location": "SF",
         "fit": "new-grad", "url": "https://anthropic.com/careers"},
        {"company": "Anthropic", "role": "Research Engineer, new grad",
         "location": "SF", "fit": "new-grad",
         "url": "https://anthropic.com/careers"},
        {"company": "Anthropic", "role": "Applied AI", "location": "SF",
         "fit": "mid", "url": "https://anthropic.com/careers"},
        {"company": "Anthropic", "role": "Infrastructure Engineer",
         "location": "SF", "fit": "mid", "url": "https://anthropic.com/careers"},
        {"company": "Anthropic", "role": "Product Engineer", "location": "NYC",
         "fit": "mid", "url": "https://anthropic.com/careers"},
    ],
    "step_elapsed": [1.0, 4.0, 9.0, 14.0, 20.0, 29.0],  # mockRun.js st_2
    "elapsed_s": 41.0,                                   # ag02 done · 41s
}

#: Databricks flavor — 3 roles, 1 new-grad (mockRun.js st_3: roles 3, newgrad 1).
_DATABRICKS = {
    "target": "databricks.com/careers",
    "roles": [
        {"company": "Databricks", "role": "SWE, new grad",
         "location": "Mtn View", "fit": "new-grad",
         "url": "https://databricks.com/careers"},
        {"company": "Databricks", "role": "Software Engineer, Backend",
         "location": "Mtn View", "fit": "mid",
         "url": "https://databricks.com/careers"},
        {"company": "Databricks", "role": "Data Engineer",
         "location": "Remote (US)", "fit": "mid",
         "url": "https://databricks.com/careers"},
    ],
    "step_elapsed": [1.0, 4.0, 10.0, 16.0, 23.0, 34.0],  # mockRun.js st_3
    "elapsed_s": 52.0,                                    # ag03 done · 52s
}

#: Generic flavor timing for unrecognized targets.
_GENERIC_STEP_ELAPSED = [1.0, 4.0, 9.0, 15.0, 20.0, 28.0]
_GENERIC_ELAPSED_S = 44.0


def _company_from_target(target: str) -> str:
    """Best-effort company label from a host/path target ('figma.com/careers' → 'Figma')."""
    host = target.removeprefix("https://").removeprefix("http://").split("/", 1)[0]
    host = host.removeprefix("www.")
    label = host.split(".", 1)[0] if host else ""
    return label.capitalize() or "Unknown"


def _flavor_for(target: str) -> Dict[str, Any]:
    """Pick the canned flavor for a target (phase-2 Task B mock spec)."""
    t = (target or "").lower()
    if "anthropic" in t:
        return _ANTHROPIC
    if "databricks" in t:
        return _DATABRICKS
    if "stripe" in t or not t:
        return _STRIPE
    # Anything else → generic 2-role extraction on that target.
    company = _company_from_target(target)
    url = target if target.startswith("http") else f"https://{target}"
    return {
        "target": target,
        "roles": [
            {"company": company, "role": "Software Engineer, new grad",
             "location": "Remote", "fit": "new-grad", "url": url},
            {"company": company, "role": "Software Engineer",
             "location": "Remote", "fit": "mid", "url": url},
        ],
        "step_elapsed": _GENERIC_STEP_ELAPSED,
        "elapsed_s": _GENERIC_ELAPSED_S,
    }


def _mock_lines(target: str, n_roles: int) -> List[str]:
    """The 6 canned step lines (phase-2 Task B, mirroring mockRun.js st_1)."""
    return [
        f"opening {target}",
        "cookie banner dismissed",
        "filtering: engineering · university",
        "reading role cards",
        f"extracting → {n_roles} roles matched",
        "collecting apply links",
    ]


class RetrieverAdapter(BaseAdapter):
    """Runs one browser subtask against an allowlisted target (D5 Zone 1).

    Frozen API (phase-2 Task B — the orchestrator calls exactly this)::

        adapter = RetrieverAdapter()
        result: AgentResult = await adapter.run_subtask(subtask, on_step=cb)
    """

    KEY_NAME = "RETRIEVER_API_KEY"

    def __init__(
        self,
        mock_step_delay: float = 0.9,
        poll_interval_s: float = POLL_INTERVAL_S,
        hard_cap_s: float = HARD_CAP_S,
    ) -> None:
        """Args:
            mock_step_delay: sleep before each canned mock step (tests pass 0).
            poll_interval_s: live-path poll cadence (default 2s per Task B).
            hard_cap_s: wall-clock cap (default 60s per Task B + D2).
        """
        self.mock_step_delay = mock_step_delay
        self.poll_interval_s = poll_interval_s
        self.hard_cap_s = hard_cap_s

    # ------------------------------------------------------------------ API

    async def run_subtask(
        self, subtask: PlanSubtask, on_step: Optional[OnStep] = None
    ) -> AgentResult:
        """Run ONE subtask → AgentResult (CONTRACTS.md §3). NEVER raises (D7).

        `on_step(step, line, elapsed_s)` is awaited on every new progress
        line; the orchestrator maps it to `agent_update` events.
        """
        try:
            if self.live:
                return await self._run_live(subtask, on_step)
            return await self._run_mock(subtask, on_step)
        except Exception as exc:  # D7 last-resort net — still well-formed.
            return AgentResult(
                subtask_id=subtask.id,
                status="failed",
                data={},
                screenshot_ref=None,
                steps_log=[f"error: {type(exc).__name__}: {exc}"],
                elapsed_s=0.0,
            )

    # ------------------------------------------------------------- live path

    async def _run_live(
        self, subtask: PlanSubtask, on_step: Optional[OnStep]
    ) -> AgentResult:
        """Real Retriever session: submit → poll every `poll_interval_s`,
        hard `hard_cap_s` wall-clock cap (phase-2 Task B + D2).

        Timeout returns status "partial" if any data was collected, else
        "failed" — steps_log notes the timeout. HTTP/network errors return
        status "failed" with the error string in steps_log. Never raises.
        """
        t0 = time.monotonic()
        deadline = t0 + self.hard_cap_s
        steps_log: List[str] = []
        data: Dict[str, Any] = {}
        screenshot_ref: Optional[str] = None
        step = 0

        def _elapsed() -> float:
            return _trunc1(time.monotonic() - t0)

        # VERIFY: base URL + routes Sat (VERIFY.md) — env overrides only,
        # never hardcoded guesses buried in logic.
        base_url = os.getenv("RETRIEVER_BASE_URL", "https://api.retriever.com")
        submit_path = os.getenv("RETRIEVER_SUBMIT_PATH", "/sessions")
        poll_path = os.getenv("RETRIEVER_POLL_PATH", "/sessions/{id}")
        # VERIFY: auth header shape Sat — assuming Bearer.
        headers = {"Authorization": f"Bearer {self.key}"}

        target = subtask.target or ""
        url = target if target.startswith("http") else f"https://{target}"

        try:
            async with httpx.AsyncClient(
                base_url=base_url, headers=headers, timeout=httpx.Timeout(15.0)
            ) as client:
                # VERIFY: submit body field names Sat (url/instruction/output_schema).
                resp = await client.post(
                    submit_path,
                    json={
                        "url": url,
                        "instruction": subtask.instruction,
                        "output_schema": subtask.output_schema,
                    },
                )
                resp.raise_for_status()
                session = resp.json()
                # VERIFY: session id field name Sat.
                session_id = str(session.get("id") or session.get("session_id") or "")
                if not session_id:
                    return AgentResult(
                        subtask_id=subtask.id,
                        status="failed",
                        data={},
                        screenshot_ref=None,
                        steps_log=steps_log + ["error: submit returned no session id"],
                        elapsed_s=_elapsed(),
                    )

                last_line: Optional[str] = None
                while True:
                    if time.monotonic() >= deadline:
                        return self._timeout_result(
                            subtask, data, screenshot_ref, steps_log, _elapsed()
                        )

                    poll = await client.get(poll_path.format(id=session_id))
                    poll.raise_for_status()
                    body = poll.json()

                    # VERIFY: progress-line field name Sat.
                    line = str(
                        body.get("step")
                        or body.get("status_line")
                        or body.get("message")
                        or body.get("status")
                        or ""
                    )
                    if line and line != last_line:
                        step += 1
                        steps_log.append(line)
                        last_line = line
                        if on_step:
                            await on_step(step, line, _elapsed())

                    if isinstance(body.get("data"), dict) and body["data"]:
                        data = body["data"]  # keep latest partial data (D7)
                    # VERIFY: screenshot field name Sat.
                    screenshot_ref = (
                        body.get("screenshot_ref") or body.get("screenshot")
                        or screenshot_ref
                    )

                    status = str(body.get("status", "")).lower()
                    if status in _TERMINAL_OK:
                        return AgentResult(
                            subtask_id=subtask.id,
                            status="ok",
                            data=data,
                            screenshot_ref=screenshot_ref,
                            steps_log=steps_log,
                            elapsed_s=_elapsed(),
                        )
                    if status in _TERMINAL_FAILED:
                        return AgentResult(
                            subtask_id=subtask.id,
                            status="partial" if data else "failed",
                            data=data,
                            screenshot_ref=screenshot_ref,
                            steps_log=steps_log + [f"agent reported: {status}"],
                            elapsed_s=_elapsed(),
                        )

                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return self._timeout_result(
                            subtask, data, screenshot_ref, steps_log, _elapsed()
                        )
                    await asyncio.sleep(min(self.poll_interval_s, remaining))
        except httpx.HTTPError as exc:
            # phase-2 Task B: HTTP/network errors → failed, error in steps_log.
            return AgentResult(
                subtask_id=subtask.id,
                status="failed",
                data=data,
                screenshot_ref=screenshot_ref,
                steps_log=steps_log + [f"error: {type(exc).__name__}: {exc}"],
                elapsed_s=_elapsed(),
            )
        except Exception as exc:  # bad JSON, format(), etc. — D7.
            return AgentResult(
                subtask_id=subtask.id,
                status="failed",
                data=data,
                screenshot_ref=screenshot_ref,
                steps_log=steps_log + [f"error: {type(exc).__name__}: {exc}"],
                elapsed_s=_elapsed(),
            )

    def _timeout_result(
        self,
        subtask: PlanSubtask,
        data: Dict[str, Any],
        screenshot_ref: Optional[str],
        steps_log: List[str],
        elapsed_s: float,
    ) -> AgentResult:
        """Well-formed timeout result (phase-2 Task B + D2): partial if any
        data was collected before the cap, else failed."""
        return AgentResult(
            subtask_id=subtask.id,
            status="partial" if data else "failed",
            data=data,
            screenshot_ref=screenshot_ref,
            steps_log=steps_log + [f"timeout: {int(self.hard_cap_s)}s hard cap reached"],
            elapsed_s=elapsed_s,
        )

    # ------------------------------------------------------------- mock path

    async def _run_mock(
        self, subtask: PlanSubtask, on_step: Optional[OnStep]
    ) -> AgentResult:
        """Canned Stripe-jobs run (phase-2 Task B), flavored by target:
        anthropic → 5 roles (2 new-grad) · databricks → 3 roles (1 new-grad)
        · stripe/empty → 3 Stripe roles · else generic 2-role extraction.

        Each of the 6 canned lines is preceded by
        `await asyncio.sleep(self.mock_step_delay)` and fires
        `on_step(step_1_based, line, elapsed)`. Elapsed values are canned to
        the mockRun.js beats so the mock demo matches the golden run (D4).
        """
        flavor = _flavor_for(subtask.target)
        roles: List[Dict[str, Any]] = flavor["roles"]
        target = subtask.target or flavor["target"]
        lines = _mock_lines(target, len(roles))

        for i, (line, canned_elapsed) in enumerate(
            zip(lines, flavor["step_elapsed"]), start=1
        ):
            await asyncio.sleep(self.mock_step_delay)
            if on_step:
                await on_step(i, line, _trunc1(canned_elapsed))

        return AgentResult(
            subtask_id=subtask.id,
            status="ok",
            data={"roles": roles},
            screenshot_ref=None,
            steps_log=lines,
            elapsed_s=_trunc1(flavor["elapsed_s"]),
        )

    # ------------------------------------------------- legacy sync interface

    def _mock(self, **kwargs: Any) -> Dict[str, Any]:
        """Legacy canned AgentResult dict (CONTRACTS.md §3) via `call()`.

        Kept for Phase 1 backwards compat (D6). New code uses `run_subtask`.
        """
        target = kwargs.get("target", "stripe.com/jobs")
        flavor = _flavor_for(target)
        return {
            "subtask_id": kwargs.get("subtask_id", "st_2"),
            "status": "ok",
            "data": {"roles": flavor["roles"]},
            "screenshot_ref": None,
            "steps_log": _mock_lines(target or flavor["target"], len(flavor["roles"])),
            "elapsed_s": _trunc1(flavor["elapsed_s"]),
        }
