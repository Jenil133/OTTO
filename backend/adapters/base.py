"""BaseAdapter — the mock-mode pattern of architecture diagram D6.

    ORCHESTRATOR ──► adapters/<sponsor>.py
      if MOCK flag or key missing ──► canned response (instant)
      else ──────────────────────────► real sponsor API

WHY (D6): credits arrived late + integrations flake → the spine must run on
ANY subset of live keys. Flip adapters to real one at a time; a broken
sponsor flips back to mock in seconds. Same trick powers `?mock=1` and the
golden replay.

Global kill-switch: `OTTO_MOCK=1` in the environment forces EVERY adapter to
mock regardless of which keys are present.
"""

from __future__ import annotations

import os
from typing import Any


class BaseAdapter:
    """One subclass per sponsor: retriever · kimi · minimax · mem0 · band ·
    respan · elevenlabs.

    Subclasses declare `KEY_NAME` (the env var holding their API key) and
    implement `_mock()`; `_real()` stays NotImplementedError until Phase 2.
    The orchestrator NEVER calls a sponsor directly — always through
    `adapter.call(...)`.
    """

    #: Name of the env var holding this sponsor's API key (see .env.example).
    KEY_NAME: str = ""

    @property
    def key(self) -> str | None:
        """The sponsor API key from the environment, or None if absent."""
        value = os.getenv(self.KEY_NAME, "")
        return value or None

    @property
    def live(self) -> bool:
        """True only when the key is present AND mock mode is off.

        `OTTO_MOCK=1` forces mock globally (D6) — a missing key degrades to
        mock silently so nobody is ever blocked.
        """
        forced_mock = os.getenv("OTTO_MOCK", "") == "1"
        return self.key is not None and not forced_mock

    def call(self, **kwargs: Any) -> Any:
        """Dispatch to `_real()` when live, else `_mock()` (D6)."""
        if self.live:
            return self._real(**kwargs)
        return self._mock(**kwargs)

    def _mock(self, **kwargs: Any) -> Any:
        """Canned response consistent with docs/CONTRACTS.md. Subclasses own this."""
        raise NotImplementedError(f"{type(self).__name__} must implement _mock()")

    def _real(self, **kwargs: Any) -> Any:
        """Real sponsor API call — authored in Phase 2+."""
        raise NotImplementedError("Phase 2")
