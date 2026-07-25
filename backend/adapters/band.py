"""Band adapter — the otto-ops room (architecture D1 side service).

Every actor (planner, webagent-1/2/3, synthesizer) posts lifecycle messages;
they mirror into the UI feed rail as `band_msg` events. Mock acks a message
per docs/CONTRACTS.md §5.

Phase 2 · Task F fallback: `post()` appends every message to the in-process
`FEED` list — "worst case internal feed alone keeps the demo alive"
(phase-2.md Task F). The real Band SDK / raw-API post attaches Saturday.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from .base import BaseAdapter

#: In-process coordination feed (phase-2 Task F fallback). Every `post()`
#: lands here FIRST — even once live — so the audit trail and the UI feed
#: rail never depend on the SDK being up (D7).
FEED: List[Dict[str, Any]] = []


class BandAdapter(BaseAdapter):
    """Posts one lifecycle message to the persistent otto-ops audit room."""

    KEY_NAME = "BAND_API_KEY"

    async def post(self, actor: str, text: str) -> Dict[str, Any]:
        """Post one lifecycle message (CONTRACTS.md §5 shape) to the feed.

        Appends ``{room, actor, text, ts}`` to the module-level `FEED` and
        returns it. `actor` is the long §5 identity
        (planner/webagent-1/synthesizer…); the orchestrator mirrors the line
        as a shortened `band_msg` event itself (CONTRACTS.md §1/§5).

        Never raises (D7) — a lost audit line must not stall the spine.
        """
        msg: Dict[str, Any] = {
            "room": os.getenv("BAND_ROOM", "otto-ops"),
            "actor": actor,
            "text": text,
            "ts": int(time.time() * 1000),
        }
        FEED.append(msg)
        # VERIFY: real Band SDK / raw-API post lands Sat (VERIFY.md — room
        # create + participant identities per phase-2 Task F). Until then the
        # internal feed alone keeps the demo alive (Task F fallback); once
        # live, post to the API here AFTER the local append so a flaky SDK
        # can never lose a line (D7).
        if self.live:
            pass  # real otto-ops room post attaches here Saturday
        return msg

    def _mock(self, **kwargs: Any) -> Dict[str, Any]:
        """Ack the Band message (CONTRACTS.md §5) without posting anywhere."""
        return {
            "posted": True,
            "room": kwargs.get("room", "otto-ops"),
            "actor": kwargs.get("actor", "planner"),
            "text": kwargs.get("text", "dispatching ×3"),
            "ts": int(time.time() * 1000),
        }
