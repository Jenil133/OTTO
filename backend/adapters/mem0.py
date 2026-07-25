"""mem0 adapter — preference memory (architecture D1 side service).

Read before plan, write after synthesize — async, never on the critical
path. Mock returns entries per docs/CONTRACTS.md §4.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base import BaseAdapter


class Mem0Adapter(BaseAdapter):
    """Semantic search over the user's durable prefs / aliases / facts."""

    KEY_NAME = "MEM0_API_KEY"

    async def read(self, text: str) -> List[str]:
        """Preference read before planning — Phase 2 stub, ALWAYS returns [].

        phase-2.md scope: "mem0 (Ph4 — a stub returns `[]`)". Even in live
        mode this stays empty so the planner gets a consistent "no known
        preferences" signal today; Phase 4 replaces it with a real mem0
        semantic search returning `text` fields of matching CONTRACTS.md §4
        entries (the `_mock()` below shows that shape).
        """
        return []

    def _mock(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Canned mem0 entries (CONTRACTS.md §4)."""
        return [
            {
                "kind": "preference",
                "text": "Bay Area or remote only",
                "request_id": "req_1832",
                "used": 2,
            },
            {
                "kind": "preference",
                "text": "Prefers new-grad level roles",
                "request_id": "req_1832",
                "used": 1,
            },
            {
                "kind": "alias",
                "text": "“the big three” → Stripe, Anthropic, Databricks",
                "request_id": "req_1790",
                "used": 3,
            },
        ]
