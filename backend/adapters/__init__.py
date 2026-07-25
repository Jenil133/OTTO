"""OTTO sponsor adapters — one per sponsor, mock-mode pattern (architecture D6).

The orchestrator never calls a sponsor directly; it always goes through
`adapter.call(...)`, which degrades to canned data when the key is missing
or `OTTO_MOCK=1` is set. The spine must run on ANY subset of live keys.
"""

from .base import BaseAdapter
from .retriever import RetrieverAdapter
from .kimi import KimiAdapter
from .minimax import MinimaxAdapter
from .mem0 import Mem0Adapter
from .band import BandAdapter
from .respan import RespanAdapter
from .elevenlabs import ElevenLabsAdapter

__all__ = [
    "BaseAdapter",
    "RetrieverAdapter",
    "KimiAdapter",
    "MinimaxAdapter",
    "Mem0Adapter",
    "BandAdapter",
    "RespanAdapter",
    "ElevenLabsAdapter",
]
