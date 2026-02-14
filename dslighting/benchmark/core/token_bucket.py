"""Async token bucket implementation for rate limiting."""

from __future__ import annotations

import asyncio
import time

__all__ = ["AsyncTokenBucket"]


class AsyncTokenBucket:
    """Simple async token bucket limiter for admission rate control."""

    def __init__(self, rate_per_second: float, burst_tokens: float):
        self.rate = max(0.1, float(rate_per_second))
        self.capacity = max(1.0, float(burst_tokens))
        self._tokens = self.capacity
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: float = 1.0) -> float:
        """Consume tokens and return waited seconds."""
        requested = max(0.1, float(tokens))
        waited = 0.0
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = max(0.0, now - self._last_refill)
                if elapsed > 0:
                    self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
                    self._last_refill = now

                if self._tokens >= requested:
                    self._tokens -= requested
                    return waited

                missing = requested - self._tokens
                sleep_seconds = max(0.01, missing / self.rate)
            await asyncio.sleep(sleep_seconds)
            waited += sleep_seconds
