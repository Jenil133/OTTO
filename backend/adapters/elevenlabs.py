"""ElevenLabs adapter — the voice edge (architecture D1, D3).

STT + TTS + the run_task() tool live OUTSIDE the pipeline (latency-critical
placement rule). The tool round-trip pattern is decided at hour zero
(VERIFY.md, D3 fallback ladder). Voice loop lands in Phase 3-B.
"""

from __future__ import annotations

from typing import Any, Dict

from .base import BaseAdapter


class ElevenLabsAdapter(BaseAdapter):
    """Speaks text (TTS) / hosts the conversational agent session."""

    KEY_NAME = "ELEVENLABS_API_KEY"

    def _mock(self, **kwargs: Any) -> Dict[str, Any]:
        """No audio in mock mode — the UI shows text; TTS arrives in Phase 3."""
        return {
            "audio_ref": None,
            "note": "mock voice — no audio synthesized; spoken text rendered in transcript only",
        }
