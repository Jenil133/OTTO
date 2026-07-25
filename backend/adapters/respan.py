"""Respan adapter — the LLM gateway (architecture D1).

Every LLM call exits through Respan → cost + latency telemetry feeds the
`telemetry` event (docs/CONTRACTS.md §1). Mock returns routing telemetry.
"""

from __future__ import annotations

from typing import Any, Dict

from .base import BaseAdapter


class RespanAdapter(BaseAdapter):
    """Routes an LLM call through the gateway and reports cost/latency."""

    KEY_NAME = "RESPAN_API_KEY"

    def _mock(self, **kwargs: Any) -> Dict[str, Any]:
        """Canned gateway telemetry — feeds the §1 `telemetry` payload."""
        return {"routed": True, "cost_usd": 0.02, "latency_ms": 840}
