import time
from collections import deque
from typing import Deque


class BudgetCircuitBreaker:
    """Sliding-window rate & invocation budget limiter to prevent runaway agent loops."""

    def __init__(self, max_calls_per_window: int = 100, window_seconds: float = 60.0):
        self.max_calls = max_calls_per_window
        self.window_seconds = window_seconds
        self._timestamps: Deque[float] = deque()

    def record_and_check(self) -> bool:
        """Returns True if within budget, False if tripped."""
        now = time.time()
        cutoff = now - self.window_seconds

        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        if len(self._timestamps) >= self.max_calls:
            return False

        self._timestamps.append(now)
        return True

    def reset(self) -> None:
        self._timestamps.clear()
