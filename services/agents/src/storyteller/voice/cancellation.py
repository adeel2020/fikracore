"""Cooperative cancellation for realtime voice turns (Phase 3C).

A single user turn (``Generation``) can be torn down at any point — barge-in,
client ``interrupt``, disconnect, or error. Cancellation here is *cooperative*:
long-running ML work (STT/TTS/conversation) is run in worker threads that cannot
be force-killed, so each stage checks ``CancellationToken`` before and after its
blocking call and discards stale results. Fresh generations are tracked by a
monotonic ``GenerationCounter`` so stale audio/transcript events can be dropped
client-side.
"""

from __future__ import annotations

import asyncio
import dataclasses
import time
from typing import Any


class Cancelled(Exception):
    """Raised by ``CancellationToken.check()`` when a turn is cancelled."""


class CancellationToken:
    """An asyncio.Event-backed cooperative cancellation flag (not awaitable-scoped)."""

    def __init__(self) -> None:
        self._event = asyncio.Event()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        """Mark the turn as cancelled (idempotent)."""
        self._event.set()

    def check(self) -> None:
        """Raise :class:`Cancelled` if this turn has been cancelled."""
        if self._event.is_set():
            raise Cancelled()

    async def wait(self) -> None:
        """Block until the token is cancelled."""
        await self._event.wait()


@dataclasses.dataclass
class Generation:
    """State for one user turn."""

    id: int
    token: CancellationToken
    created_at: float = dataclasses.field(default_factory=time.perf_counter)
    timings: dict[str, float] = dataclasses.field(default_factory=dict)
    meta: dict[str, Any] = dataclasses.field(default_factory=dict)

    def cancel(self) -> None:
        self.token.cancel()

    @property
    def cancelled(self) -> bool:
        return self.token.cancelled

    def check(self) -> None:
        self.token.check()


class GenerationCounter:
    """Monotonic, per-connection source of generation ids and tokens."""

    def __init__(self) -> None:
        self._counter = 0

    def next(self) -> Generation:
        """Return the next generation with a fresh, uncancelled token."""
        self._counter += 1
        return Generation(id=self._counter, token=CancellationToken())


__all__ = ["Cancelled", "CancellationToken", "Generation", "GenerationCounter"]