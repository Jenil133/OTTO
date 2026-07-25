"""MiniMax M3 synthesizer adapter (architecture D1 step [3], phase-2 Task C).

Merges every subtask's AgentResult (CONTRACTS.md §3) — ok, partial AND
failed — into the frozen §1 `result` payload: `spoken` (≤3 sentences) plus a
results `card`. Two paths per the D6 mock/live pattern:

    self.live  -> one chat-completion POST to MiniMax M3, system prompt =
                  backend/prompts/synthesizer.md, strict-JSON reply parsed
                  into schemas.ResultPayload.
    else       -> pure-code mock composition, instant, no network.

D7 rule: NOTHING here ever raises into the orchestrator. Any live-path
failure (network, HTTP, JSON parse, schema validation) falls back to the
mock composition over the same inputs, so a well-formed ResultPayload
always comes back.

Legacy surface: `call()` / `_mock()` from Phase 1 keep working unchanged so
older callers (and the golden replay) never break.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import httpx

from schemas import AgentResult, Plan, ResultCard, ResultPayload

from .base import BaseAdapter

#: Loaded verbatim as the system prompt (phase-2 Task C — judged PDD artifact).
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "synthesizer.md"

#: Canonical jobs-flavor column order (CONTRACTS.md §1 `result.card.columns`).
_JOBS_COLUMNS = ("company", "role", "location", "fit")

#: Spelled-out small counts for the honest all-failed line.
_COUNT_WORDS = {1: "one", 2: "two", 3: "three"}


#: TokenRouter — the same OpenAI-compatible gateway the planner uses. When no
#: native MINIMAX_API_KEY is set, the synthesizer routes MiniMax M3 through
#: TokenRouter so ONE key powers the whole brain (planner + synthesizer) and
#: gets TokenRouter's automatic multi-provider failover.
_DEFAULT_TOKENROUTER_BASE = "https://api.tokenrouter.com/v1"


class MinimaxAdapter(BaseAdapter):
    """Synthesizes agent results into the spoken answer + results card.

    Live creds resolve in this order (D6): a native MINIMAX_API_KEY (talks to
    MiniMax directly) else TOKENROUTER_API_KEY (routes M3 through the same
    gateway as the planner). Either present -> live; neither -> mock.
    """

    KEY_NAME = "MINIMAX_API_KEY"

    @property
    def live(self) -> bool:
        """Live when a MiniMax OR TokenRouter key is present and OTTO_MOCK is
        off — the synthesizer can reach M3 through either path."""
        forced_mock = os.getenv("OTTO_MOCK", "") == "1"
        has_key = bool(os.getenv("MINIMAX_API_KEY") or os.getenv("TOKENROUTER_API_KEY"))
        return has_key and not forced_mock

    def _resolve_gateway(self) -> tuple[str, str]:
        """Return (chat-completions endpoint URL, api key) for the live call.

        Native MiniMax if MINIMAX_API_KEY is set (uses MINIMAX_BASE_URL, a full
        chat-completion path); otherwise the OpenAI-compatible TokenRouter route
        `{base}/chat/completions` with the TokenRouter key.
        """
        minimax_key = os.getenv("MINIMAX_API_KEY")
        if minimax_key:
            # VERIFY: native MiniMax endpoint + payload shape (Sat).
            endpoint = os.getenv(
                "MINIMAX_BASE_URL",
                "https://api.minimax.io/v1/text/chatcompletion_v2",
            )
            return endpoint, minimax_key
        # TokenRouter path (OpenAI-compatible): base + /chat/completions.
        base = (
            os.getenv("TOKENROUTER_BASE_URL") or _DEFAULT_TOKENROUTER_BASE
        ).rstrip("/")
        return f"{base}/chat/completions", os.getenv("TOKENROUTER_API_KEY", "")

    # ------------------------------------------------------------------
    # Frozen orchestrator API (phase-2 Task C)
    # ------------------------------------------------------------------

    async def synthesize(
        self,
        request_id: str,
        user_text: str,
        plan: Plan,
        results: List[AgentResult],
        elapsed_s: float,
    ) -> ResultPayload:
        """One call merging ALL subtask results into the §1 `result` payload.

        Dispatches on `self.live` itself (D6): real MiniMax M3 chat
        completion when a key is present and OTTO_MOCK is off, otherwise the
        instant pure-code composition. Never raises (D7) — every failure
        path degrades to the mock composition on the same inputs.
        """
        if self.live:
            try:
                return await self._synthesize_live(
                    request_id, user_text, plan, results, elapsed_s
                )
            except Exception as exc:
                # D7: parse/network/validation failure -> honest pure-code
                # composition over the same inputs. Never crash the spine.
                logging.getLogger("otto.minimax").warning(
                    "synthesizer live call failed: %s", exc
                )
                return self._compose(request_id, plan, results, elapsed_s)
        return self._compose(request_id, plan, results, elapsed_s)

    # ------------------------------------------------------------------
    # Live path — MiniMax M3 chat completion (phase-2 Task C bullet 1-3)
    # ------------------------------------------------------------------

    async def _synthesize_live(
        self,
        request_id: str,
        user_text: str,
        plan: Plan,
        results: List[AgentResult],
        elapsed_s: float,
    ) -> ResultPayload:
        """POST one chat completion to MiniMax M3 and parse the strict-JSON
        reply `{spoken, card:{columns, rows}, sources, status}` into a
        ResultPayload (CONTRACTS.md §1 `result`).

        All real-API specifics are env-overridable pending Saturday's
        VERIFY.md answers — nothing is a buried hardcoded guess.
        """
        # Native MiniMax or TokenRouter gateway (see _resolve_gateway).
        endpoint, api_key = self._resolve_gateway()
        # VERIFY: exact M3 model string — in TokenRouter's catalog (MiniMax row)
        # or the MiniMax console. Set MINIMAX_MODEL to it.
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M3")
        # M3 also emits a <think> reasoning block before its JSON, so keep the
        # ceiling generous (same lesson as the planner's KIMI_TIMEOUT_S).
        timeout_s = float(os.getenv("MINIMAX_TIMEOUT_S", "75"))

        body: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._load_prompt()},
                {
                    "role": "user",
                    "content": self._build_user_content(user_text, plan, results),
                },
            ],
            # VERIFY: MiniMax JSON-mode / response_format flag name (Sat).
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(endpoint, json=body, headers=headers)
            resp.raise_for_status()
            raw = resp.json()

        # VERIFY: reply shape — assuming OpenAI-style choices[0].message.content (Sat).
        text = raw["choices"][0]["message"]["content"]
        parsed = json.loads(self._strip_fences(text))

        return ResultPayload(
            request_id=request_id,
            status=parsed["status"],
            spoken=parsed["spoken"],
            card=ResultCard(**parsed["card"]),
            sources=parsed.get("sources", []),
            elapsed_s=elapsed_s,
            cost_usd=0.0,  # placeholder until Respan telemetry lands (Phase 4)
            agents=len(results),
        )

    def _build_user_content(
        self, user_text: str, plan: Plan, results: List[AgentResult]
    ) -> Any:
        """Build the user message: JSON dump of {user_text, plan subtask
        titles, results (status+data+steps_log)} per phase-2 Task C.

        Screenshot-recovery branch (phase-2 Task C bullet 3, STUB): a result
        with empty `data` but a `screenshot_ref` gets its screenshot appended
        as a multimodal image content block so M3 can extract from pixels.
        """
        payload = {
            "user_text": user_text,
            "plan_subtask_titles": [st.title for st in plan.subtasks],
            "results": [
                {"status": r.status, "data": r.data, "steps_log": r.steps_log}
                for r in results
            ],
        }
        user_json = json.dumps(payload, ensure_ascii=False)

        image_blocks: List[Dict[str, Any]] = []
        for r in results:
            if not r.data and r.screenshot_ref:
                # UNTESTED: multimodal path awaits MiniMax image-input format
                # from VERIFY.md — assuming OpenAI-style image_url blocks.
                image_blocks.append(
                    {"type": "image_url", "image_url": {"url": r.screenshot_ref}}
                )
        if image_blocks:
            return [{"type": "text", "text": user_json}, *image_blocks]
        return user_json

    @staticmethod
    def _load_prompt() -> str:
        """Read prompts/synthesizer.md — the system prompt. Missing file
        degrades to a one-line instruction instead of crashing (D7)."""
        try:
            return _PROMPT_PATH.read_text(encoding="utf-8")
        except OSError:
            return (
                "Merge the agent results into strict JSON "
                '{"spoken", "card": {"columns", "rows"}, "sources", "status"}. '
                "Never invent data; admit failures honestly."
            )

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Tolerate a model that wraps its strict JSON in ``` fences, a
        leading reasoning block, and/or TRAILING prose after the object.
        CONFIRMED live: MiniMax M3 via TokenRouter prepends an un-fenced
        ``<think>...</think>`` block, and occasionally appends trailing text
        after a perfectly valid JSON object (e.g. a follow-up sentence) —
        that trailing text can itself start with ``{``-like punctuation, so
        a plain ``startswith("{")`` check is not enough to skip extraction."""
        t = text.strip()
        if "<think>" in t and "</think>" in t:
            t = t.split("</think>", 1)[1].strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[1] if "\n" in t else ""
            t = t.rstrip()
            if t.endswith("```"):
                t = t[:-3]
        t = t.strip()
        # Always extract the first BALANCED {...} object — handles both
        # leading prose and trailing prose, and ignores stray braces that
        # might appear in text after the real object closes.
        start = t.find("{")
        if start != -1:
            depth = 0
            for i in range(start, len(t)):
                if t[i] == "{":
                    depth += 1
                elif t[i] == "}":
                    depth -= 1
                    if depth == 0:
                        t = t[start : i + 1]
                        break
        return t.strip()

    # ------------------------------------------------------------------
    # Mock path — pure-code composition, instant (phase-2 Task C mock rules)
    # ------------------------------------------------------------------

    def _compose(
        self,
        request_id: str,
        plan: Plan,
        results: List[AgentResult],
        elapsed_s: float,
    ) -> ResultPayload:
        """Deterministic merge of AgentResults (CONTRACTS.md §3) into the §1
        `result` payload — also the D7 fallback for any live-path failure.

        Rules (phase-2 Task C mock path):
          rows    = flatten of every result's `data["roles"]` (or any
                    list-valued data key) — only real extracted data.
          columns = first row's keys, ordered company/role/location/fit
                    when the rows look like jobs.
          status  = ok if all ok · failed if all failed (or nothing ran) ·
                    else partial.
          sources = plan targets of the non-failed results only.
        """
        rows = self._flatten_rows(results)
        columns = self._infer_columns(rows)
        statuses = [r.status for r in results]

        if results and all(s == "ok" for s in statuses):
            status = "ok"
        elif not results or all(s == "failed" for s in statuses):
            status = "failed"
        else:
            status = "partial"

        n_sites = len(results)
        if status == "failed":
            count_word = _COUNT_WORDS.get(n_sites, str(n_sites))
            spoken = (
                f"I could not get into any of the {count_word} sites this time — "
                "nothing extracted, so no guesses. Want me to retry?"
            )
        else:
            newgrad = sum(1 for row in rows if row.get("fit") == "new-grad")
            spoken = (
                f"Found {len(rows)} roles across the {n_sites} sites — "
                f"{newgrad} look new-grad friendly. Want the links?"
            )
            if status == "partial":
                spoken += " One site did not finish — this is what came back."

        target_by_id = {st.id: st.target for st in plan.subtasks}
        sources = list(
            dict.fromkeys(
                target_by_id[r.subtask_id]
                for r in results
                if r.status != "failed" and r.subtask_id in target_by_id
            )
        )

        return ResultPayload(
            request_id=request_id,
            status=status,
            spoken=spoken,
            card=ResultCard(columns=columns, rows=rows),
            sources=sources,
            elapsed_s=elapsed_s,
            cost_usd=0.0,  # placeholder until Respan telemetry lands (Phase 4)
            agents=len(results),
        )

    @staticmethod
    def _flatten_rows(results: List[AgentResult]) -> List[Dict[str, Any]]:
        """Flatten each result's `data["roles"]` — or, failing that, its
        first list-valued data key — into one row list. Failed/empty results
        contribute nothing; nothing is ever fabricated (D7)."""
        rows: List[Dict[str, Any]] = []
        for r in results:
            items = r.data.get("roles")
            if not isinstance(items, list):
                items = next(
                    (v for v in r.data.values() if isinstance(v, list)), []
                )
            rows.extend(item for item in items if isinstance(item, dict))
        return rows

    @staticmethod
    def _infer_columns(rows: List[Dict[str, Any]]) -> List[str]:
        """Columns from the first row's keys; jobs rows get the canonical
        company/role/location/fit order (CONTRACTS.md §1 `result.card`)."""
        if not rows:
            return list(_JOBS_COLUMNS)  # stable empty-card header for the UI
        first = rows[0]
        if "company" in first and "role" in first:
            return [c for c in _JOBS_COLUMNS if c in first]
        return list(first.keys())

    # ------------------------------------------------------------------
    # Legacy Phase 1 surface — unchanged so `call()` keeps working (D6)
    # ------------------------------------------------------------------

    def _mock(self, **kwargs: Any) -> Dict[str, Any]:
        """Canned result payload (CONTRACTS.md §1 `result`) — legacy Phase 1
        mock, still reachable via `BaseAdapter.call()`."""
        return {
            "request_id": kwargs.get("request_id", "req_1832"),
            "status": "ok",
            "spoken": "Found 12 roles across three sites — 5 look new-grad friendly. Want the links?",
            "card": {
                "columns": ["company", "role", "location", "fit"],
                "rows": [
                    {
                        "company": "Stripe",
                        "role": "SWE, new grad",
                        "location": "SF",
                        "fit": "new-grad",
                        "url": "https://stripe.com/jobs",
                    },
                    {
                        "company": "Anthropic",
                        "role": "Software Engineer, Early Career",
                        "location": "SF",
                        "fit": "new-grad",
                        "url": "https://anthropic.com/careers",
                    },
                    {
                        "company": "Databricks",
                        "role": "SWE, University Grad",
                        "location": "Mountain View",
                        "fit": "new-grad",
                        "url": "https://databricks.com/careers",
                    },
                ],
            },
            "sources": ["stripe.com/jobs", "anthropic.com/careers", "databricks.com/careers"],
            "elapsed_s": 62,
            "cost_usd": 0.11,
            "agents": 3,
        }

    def _real(self, **kwargs: Any) -> Dict[str, Any]:
        """Legacy sync surface has no live implementation — real synthesis is
        the async `synthesize()`. Degrade to the canned mock, never crash (D7)."""
        return self._mock(**kwargs)
