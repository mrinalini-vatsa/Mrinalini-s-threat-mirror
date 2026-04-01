import asyncio
from dataclasses import dataclass


@dataclass
class MetricsStore:
    failures: int = 0
    total_processing_time_ms: float = 0.0
    processed_count: int = 0
    alerts_blocked_count: int = 0

    def __post_init__(self) -> None:
        self._lock = asyncio.Lock()

    async def record_failure(self) -> None:
        async with self._lock:
            self.failures += 1

    async def record_processing_time(self, value_ms: float) -> None:
        async with self._lock:
            self.total_processing_time_ms += value_ms
            self.processed_count += 1

    async def record_blocked_alert(self) -> None:
        async with self._lock:
            self.alerts_blocked_count += 1

    async def snapshot(self) -> tuple[int, float, int]:
        async with self._lock:
            avg = self.total_processing_time_ms / self.processed_count if self.processed_count else 0.0
            return self.failures, avg, self.alerts_blocked_count


metrics_store = MetricsStore()
