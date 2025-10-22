import asyncio
import time
from collections import deque

class AsyncRateLimiter:
    def __init__(self, max_calls: int = 10, per_seconds: float = 60.0):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self._calls = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        while True:
            async with self._lock:
                now = time.monotonic()
                while self._calls and (now - self._calls[0]) > self.per_seconds:
                    self._calls.popleft()
                if len(self._calls) < self.max_calls:
                    self._calls.append(now)
                    return
                wait_for = self.per_seconds - (now - self._calls[0]) + 0.01
            await asyncio.sleep(max(0.0, wait_for))