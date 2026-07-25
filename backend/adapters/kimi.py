"""Planner adapter — any model, via the TokenRouter/Respan gateway (phase-2 Task A).

Model is chosen by env (`PLANNER_MODEL`), not by class: the gateway is
OpenAI-compatible so swapping planners is a one-line config change. Currently
`google/gemini-3.5-flash-lite` — picked on measured latency, see the benchmark
table below. (Module/class keep the `kimi` name for import stability.)


Pipeline step [1] (architecture D1): typed text + mem0 preferences in,
`Plan | Clarification` out (docs/CONTRACTS.md §2 — the Plan object is the
same shape as the §1 ``plan`` event payload).

Modes (architecture D6, BaseAdapter pattern):

* **live** (``TOKENROUTER_API_KEY`` present, ``OTTO_MOCK`` unset) — one
  OpenAI-compatible ``chat/completions`` POST in JSON mode, system prompt =
  ``prompts/planner.md`` with the current allowlist substituted in.
* **mock** (no key / ``OTTO_MOCK=1``) — deterministic canned plans so the
  spine runs with zero keys and zero network, today.

Failure policy (architecture D7): ``plan()`` NEVER raises. Malformed model
JSON gets ONE retry with the validation error appended; a second failure —
or any transport error — returns a well-formed :class:`Clarification`.

Legacy compat: the Phase-1 sync ``call()``/``_mock()`` path is preserved
unchanged for anything still calling ``adapter.call(...)``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import httpx
from pydantic import ValidationError

from schemas import Clarification, Plan, PlanSubtask, load_allowlist_targets

#: Back-compat alias — the allowlist loader now lives in schemas (single source
#: of truth shared with the pydantic gate). Kept so existing importers work.
_load_allowlist_targets = load_allowlist_targets

from .base import BaseAdapter

# ---------------------------------------------------------------------------
# VERIFY-flagged assumptions (VERIFY.md, answered Saturday 9:00-9:45).
# Every one is an env-var override with a loud default — never a guess buried
# in logic (phase-2 Task A hard rule).
# ---------------------------------------------------------------------------

# TokenRouter base URL — CONFIRMED at the event: OpenAI-compatible gateway at
# api.tokenrouter.com/v1 (just switch base_url + one key). Overridable via env.
_DEFAULT_TOKENROUTER_BASE = "https://api.tokenrouter.com/v1"

# Planner model, selected by BENCHMARK through the TokenRouter gateway (all 5
# run on the same key + same prompt, measured live):
#
#   google/gemini-3.5-flash-lite   2.8s   3 subtasks   <- chosen
#   openai/gpt-5.4-mini            3.9s   1 subtask    (breaks the fan-out visual)
#   x-ai/grok-4.1-fast             7.6s   3 subtasks
#   z-ai/glm-5-turbo              10.4s   3 subtasks
#   moonshotai/kimi-k3            28.0s   3 subtasks   (reasoning model — 10x slower)
#
# Kimi K3 plans correctly but spends reasoning tokens the planner does not need
# (D2 budgets this stage at 5-10s). Swap models with one env var, no code change
# — that IS the TokenRouter story.
_DEFAULT_PLANNER_MODEL = "google/gemini-3.5-flash-lite"

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "planner.md"
_ALLOWLIST_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "ALLOWLIST.md"
)

#: Fallback targets if docs/ALLOWLIST.md is unreadable — mirrors its seed rows.
_FALLBACK_ALLOWLIST = [
    "stripe.com/jobs",
    "anthropic.com/careers",
    "databricks.com/careers",
]

_FALLBACK_QUESTION = "Could you rephrase that? I need a clearer goal."

# --- mock-mode vocabulary ---------------------------------------------------

#: keyword -> (allowlisted-style careers target, display name)
_COMPANY_TARGETS: Dict[str, tuple[str, str]] = {
    "stripe": ("stripe.com/jobs", "Stripe"),
    "anthropic": ("anthropic.com/careers", "Anthropic"),
    "databricks": ("databricks.com/careers", "Databricks"),
    "figma": ("figma.com/careers", "Figma"),
    "notion": ("notion.so/careers", "Notion"),
    "hn": ("news.ycombinator.com", "HN Who's Hiring"),
    "hacker news": ("news.ycombinator.com", "HN Who's Hiring"),
}

_SHOPPING_WORDS = {"buy", "price", "prices", "cheapest", "cheap", "deal", "deals", "cost", "shop", "order"}
_JOBS_WORDS = {"job", "jobs", "role", "roles", "career", "careers", "hiring", "intern", "internship", "sde", "swe", "engineer", "engineering", "grad"}

_ROLES_SCHEMA: Dict[str, Any] = {
    "roles": [{"company": "str", "role": "str", "location": "str", "fit": "str", "url": "str"}]
}
_ITEMS_SCHEMA: Dict[str, Any] = {
    "items": [{"name": "str", "price_usd": "float", "in_stock": "bool", "url": "str"}]
}


def _system_prompt() -> str:
    """prompts/planner.md with ``{{ALLOWLIST}}`` substituted (phase-2 Task A:
    the static system prompt the context-caching flag applies to). Uses the
    shared schemas.load_allowlist_targets so the prompt and the pydantic gate
    can never drift apart."""
    try:
        template = _PROMPT_PATH.read_text(encoding="utf-8")
    except OSError:
        template = "You are Otto's planner. Output strict Plan JSON only.\nAllowed targets:\n{{ALLOWLIST}}"
    bullet_list = "\n".join(f"- {t}" for t in load_allowlist_targets())
    return template.replace("{{ALLOWLIST}}", bullet_list)


class KimiAdapter(BaseAdapter):
    """Plans a request into at most 3 read-only, allowlisted subtasks."""

    KEY_NAME = "TOKENROUTER_API_KEY"

    # ------------------------------------------------------------------ #
    # Public API (frozen — the orchestrator calls exactly this)          #
    # ------------------------------------------------------------------ #

    async def plan(
        self, text: str, memory: list[str], request_id: str
    ) -> Plan | Clarification:
        """Turn one utterance + mem0 preferences into a Plan (CONTRACTS.md §2)
        or a Clarification (phase-2 Task A honesty path). Never raises (D7)."""
        if self.live:
            return await self._plan_real(text, memory, request_id)
        return await self._plan_mock(text, memory, request_id)

    # ------------------------------------------------------------------ #
    # Real path — OpenAI-compatible chat.completions via TokenRouter,    #
    # optionally through the Respan gateway (phase-2 Task A)             #
    # ------------------------------------------------------------------ #

    async def _plan_real(
        self, text: str, memory: list[str], request_id: str
    ) -> Plan | Clarification:
        """One JSON-mode completion; ONE self-repair retry on bad JSON; any
        second failure or transport error -> Clarification, never a raise."""
        # VERIFY: Respan routes Kimi (VERIFY.md "Respan / Which providers").
        # If confirmed Sat we set RESPAN_BASE_URL; else TokenRouter direct.
        base_url = (
            os.getenv("RESPAN_BASE_URL")
            or os.getenv("TOKENROUTER_BASE_URL")
            or _DEFAULT_TOKENROUTER_BASE
        ).rstrip("/")
        # PLANNER_MODEL wins; KIMI_MODEL kept as a legacy alias so an existing
        # .env keeps working. Any TokenRouter catalog id is valid here.
        model = (
            os.getenv("PLANNER_MODEL")
            or os.getenv("KIMI_MODEL")
            or _DEFAULT_PLANNER_MODEL
        )

        headers = {"Authorization": f"Bearer {self.key}"}
        # VERIFY: context-caching marker for the static system prompt — exact
        # header confirmed Sat (VERIFY.md "context-caching flag"). Coded behind
        # TOKENROUTER_CACHE_FLAG; absent = skip entirely. Accepts either
        # "Header-Name: value" or a bare value (-> X-TokenRouter-Cache).
        cache_flag = os.getenv("TOKENROUTER_CACHE_FLAG", "")
        if cache_flag:
            if ":" in cache_flag:
                name, _, value = cache_flag.partition(":")
                headers[name.strip()] = value.strip()
            else:
                headers["X-TokenRouter-Cache"] = cache_flag.strip()

        prefs = ", ".join(memory) if memory else "none"
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": f"{text}\nknown preferences: {prefs}"},
        ]

        log = logging.getLogger("otto.kimi")
        # CONFIRMED live: Kimi K3 is a reasoning model — it spends reasoning
        # tokens before answering, so a 30s ceiling times out intermittently
        # (~40% of planner calls). 75s default keeps us inside the D2 budget
        # while surviving a slow reasoning pass. Override with KIMI_TIMEOUT_S.
        timeout_s = float(os.getenv("KIMI_TIMEOUT_S", "75"))

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            for attempt in range(2):  # ONE retry max (phase-2 Task A)
                try:
                    resp = await client.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json={
                            "model": model,
                            "messages": messages,
                            # CONFIRMED live: response_format json_object works
                            # on Kimi K3 via TokenRouter. No "temperature" key —
                            # this model 400s unless temperature is exactly 1,
                            # so we omit it and take the provider default.
                            "response_format": {"type": "json_object"},
                        },
                    )
                    resp.raise_for_status()
                    content = resp.json()["choices"][0]["message"]["content"]
                except Exception as exc:
                    # Transport / HTTP error. A timeout or a blip is worth ONE
                    # retry (unchanged messages) rather than an instant
                    # Clarification — the ask was fine, the network wasn't.
                    log.warning(
                        "planner call failed (attempt %d/2): %s: %s",
                        attempt + 1,
                        type(exc).__name__,
                        exc,
                    )
                    if attempt == 1:
                        break
                    continue

                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and data.get("clarification_needed"):
                        return Clarification(
                            question=str(data.get("question") or _FALLBACK_QUESTION)
                        )
                    data["request_id"] = request_id
                    return Plan.model_validate(data)
                except (json.JSONDecodeError, ValidationError, TypeError) as err:
                    log.warning(
                        "planner returned unusable JSON (attempt %d/2): %s",
                        attempt + 1,
                        err,
                    )
                    if attempt == 1:
                        break  # second failure -> honesty path below
                    # Self-repair: feed the error back once (Task A).
                    messages.append({"role": "assistant", "content": str(content)})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Your previous reply was not valid Plan JSON. "
                                f"Error: {err}. Respond again with ONLY the "
                                "corrected JSON object — no prose."
                            ),
                        }
                    )
        # Both attempts exhausted — honest clarifying question, never a crash (D7).
        return Clarification(question=_FALLBACK_QUESTION)

    # ------------------------------------------------------------------ #
    # Mock path — deterministic, no keys, no network (D6)                #
    # ------------------------------------------------------------------ #

    async def _plan_mock(
        self, text: str, memory: list[str], request_id: str
    ) -> Plan | Clarification:
        """Believable canned planning so the spine demos with zero keys.

        Routing (phase-2 Task A mock spec): ambiguity triggers ->
        Clarification; known company mentions -> their careers targets;
        shopping words -> price-check subtasks; default -> the canonical
        job-hunt 3-subtask plan matching frontend/src/mockRun.js.
        """
        await asyncio.sleep(0.15)  # realistic pacing, still instant-ish

        lowered = text.lower().strip()
        words = lowered.split()

        companies: List[tuple[str, str]] = []
        seen_targets: set[str] = set()
        for keyword, (target, name) in _COMPANY_TARGETS.items():
            if re.search(rf"\b{re.escape(keyword)}\b", lowered) and target not in seen_targets:
                companies.append((target, name))
                seen_targets.add(target)
        companies = companies[:3]

        cleaned = [w.strip(".,!?$") for w in words]
        shopping = any(w in _SHOPPING_WORDS for w in cleaned)
        jobsy = any(w in _JOBS_WORDS for w in cleaned)
        has_topic = bool(companies) or shopping or jobsy

        # --- ambiguity triggers -> honest clarifying question (D7) ---
        ambiguous = (
            "something good" in lowered
            or re.search(r"\bstuff\b", lowered) is not None
            or ("help me" in lowered and not has_topic)
            or (len(words) < 4 and not has_topic)
        )
        if ambiguous:
            return Clarification(
                question=(
                    "Happy to help — what exactly should I look for, and on "
                    "what kind of site? For example: jobs at a company, or a "
                    "product to price-check."
                )
            )

        recall = ["new-grad", "bay area"]  # jobs-flavored runs only

        if companies:
            subtasks = [
                PlanSubtask(
                    id=f"st_{i}",
                    target=target,
                    title=f"{name} new-grad / early-career roles",
                    steps_total=6,
                    instruction=(
                        f"Open {target}, navigate to engineering openings, "
                        "filter for new-grad / early-career, and extract role "
                        "title, location, and apply link for each match."
                    ),
                    success_criteria=(
                        "At least one role extracted with title, location, and "
                        "URL — or an explicit confirmation none exist."
                    ),
                    output_schema=dict(_ROLES_SCHEMA),
                )
                for i, (target, name) in enumerate(companies, start=1)
            ]
            n = len(subtasks)
            site_word = "site" if n == 1 else "sites"
            return Plan(
                request_id=request_id,
                spoken_ack=f"On it — checking {n} careers {site_word}.",
                recall=list(recall),
                subtasks=subtasks,
            )

        if shopping:
            subtasks = [
                PlanSubtask(
                    id=f"st_{i}",
                    target=target,
                    title=f"Price check on {target}: {text.strip()}",
                    steps_total=6,
                    instruction=(
                        f"Open {target}, search for the requested product "
                        f"({text.strip()}), and extract name, current price, "
                        "stock status, and product URL for the best matches. "
                        "Read-only — never add to cart or purchase."
                    ),
                    success_criteria=(
                        "At least one matching product extracted with name, "
                        "price, and URL — or an explicit no-match confirmation."
                    ),
                    output_schema=dict(_ITEMS_SCHEMA),
                )
                # Allowlisted-style shopping backups (ALLOWLIST.md grows Sat, Task B).
                for i, target in enumerate(["bestbuy.com", "newegg.com"], start=1)
            ]
            return Plan(
                request_id=request_id,
                spoken_ack="On it — comparing prices across two stores.",
                recall=[],  # shopping runs don't echo job preferences
                subtasks=subtasks,
            )

        # --- default: canonical job-hunt plan (mockRun.js golden run) ---
        canonical = [
            ("stripe.com/jobs", "Stripe new-grad SWE roles", "Stripe"),
            ("anthropic.com/careers", "Anthropic early-career roles", "Anthropic"),
            ("databricks.com/careers", "Databricks new-grad SWE roles", "Databricks"),
        ]
        subtasks = [
            PlanSubtask(
                id=f"st_{i}",
                target=target,
                title=title,
                steps_total=6,
                instruction=(
                    f"Open {target}, navigate to engineering openings, filter "
                    "for new-grad / early-career, and extract role title, "
                    "location, and apply link for each match."
                ),
                success_criteria=(
                    "At least one role extracted with title, location, and URL "
                    "— or an explicit confirmation none exist."
                ),
                output_schema=dict(_ROLES_SCHEMA),
            )
            for i, (target, title, _name) in enumerate(canonical, start=1)
        ]
        return Plan(
            request_id=request_id,
            spoken_ack="On it — three agents out. Bay Area only, like last time.",
            recall=list(recall),
            subtasks=subtasks,
        )

    # ------------------------------------------------------------------ #
    # Legacy Phase-1 sync path — unchanged, still served by call() (D6)  #
    # ------------------------------------------------------------------ #

    def _mock(self, **kwargs: Any) -> Dict[str, Any]:
        """Canned Plan dict (CONTRACTS.md §2) — the golden job-hunt run.

        Kept verbatim for backwards compat with ``adapter.call(...)``; new
        code uses the async :meth:`plan` above.
        """
        return {
            "request_id": kwargs.get("request_id", "req_1832"),
            "spoken_ack": "On it — three agents out. Bay Area only, like last time.",
            "subtasks": [
                {
                    "id": "st_1",
                    "target": "stripe.com/jobs",
                    "title": "Stripe new-grad SWE roles",
                    "steps_total": 6,
                },
                {
                    "id": "st_2",
                    "target": "anthropic.com/careers",
                    "title": "Anthropic early-career engineering roles",
                    "steps_total": 6,
                },
                {
                    "id": "st_3",
                    "target": "databricks.com/careers",
                    "title": "Databricks new-grad SWE openings",
                    "steps_total": 6,
                },
            ],
        }
