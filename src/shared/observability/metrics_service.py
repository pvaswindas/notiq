from __future__ import annotations

import asyncio
import logging
import threading
from collections import Counter
from dataclasses import dataclass

from redis.asyncio import Redis


CORE_COUNTERS: tuple[str, ...] = (
    "notifications_received_total",
    "notifications_processed_total",
    "notifications_success_total",
    "notifications_failed_total",
    "notifications_retried_total",
    "notifications_rate_limited_total",
    "dead_letter_total",
)

WORKER_COUNTERS: tuple[str, ...] = (
    "jobs_polled",
    "worker_idle_cycles",
)

WORKER_GAUGES: tuple[str, ...] = ("jobs_processed_per_cycle",)

DEFAULT_COUNTERS: tuple[str, ...] = CORE_COUNTERS + WORKER_COUNTERS
DEFAULT_GAUGES: tuple[str, ...] = WORKER_GAUGES


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    counters: dict[str, int]
    gauges: dict[str, int]

    def as_dict(self) -> dict[str, int]:
        return {**self.counters, **self.gauges}


class MetricsBackend:
    """Minimal backend interface for MetricsService.

    Backends must keep `increment()` / `set_gauge()` non-blocking.
    """

    def increment(self, name: str, amount: int = 1) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def set_gauge(self, name: str, value: int) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def snapshot(self, counters: list[str], gauges: list[str]) -> MetricsSnapshot:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryMetricsBackend(MetricsBackend):
    def __init__(self) -> None:
        self._counter = Counter()
        self._gauges: dict[str, int] = {}
        self._lock = threading.Lock()

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counter[name] += amount

    def set_gauge(self, name: str, value: int) -> None:
        with self._lock:
            self._gauges[name] = int(value)

    async def snapshot(self, counters: list[str], gauges: list[str]) -> MetricsSnapshot:
        with self._lock:
            counters_out = {name: int(self._counter.get(name, 0)) for name in counters}
            gauges_out = {name: int(self._gauges.get(name, 0)) for name in gauges}
        return MetricsSnapshot(counters=counters_out, gauges=gauges_out)


class RedisMetricsBackend(MetricsBackend):
    def __init__(self, redis: Redis, namespace: str = "metrics:notiq") -> None:
        self._redis = redis
        self._namespace = namespace.rstrip(":")
        self._logger = logging.getLogger(__name__)

    def increment(self, name: str, amount: int = 1) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        key = self._key(name)
        task = loop.create_task(self._redis.incrby(key, int(amount)))
        task.add_done_callback(self._swallow_task_exception)

    def set_gauge(self, name: str, value: int) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        key = self._key(name)
        task = loop.create_task(self._redis.set(key, int(value)))
        task.add_done_callback(self._swallow_task_exception)

    async def snapshot(self, counters: list[str], gauges: list[str]) -> MetricsSnapshot:
        counter_keys = [self._key(name) for name in counters]
        gauge_keys = [self._key(name) for name in gauges]

        counter_values = await self._redis.mget(counter_keys) if counter_keys else []
        gauge_values = await self._redis.mget(gauge_keys) if gauge_keys else []

        counters_out: dict[str, int] = {}
        for name, raw in zip(counters, counter_values, strict=False):
            counters_out[name] = int(raw or 0)

        gauges_out: dict[str, int] = {}
        for name, raw in zip(gauges, gauge_values, strict=False):
            gauges_out[name] = int(raw or 0)

        return MetricsSnapshot(counters=counters_out, gauges=gauges_out)

    def _key(self, name: str) -> str:
        return f"{self._namespace}:{name}"

    def _swallow_task_exception(self, task: asyncio.Task[object]) -> None:
        try:
            task.result()
        except Exception as exc:
            self._logger.debug("metrics backend task failed: %s", exc)


class MetricsService:
    """Lightweight metrics façade used by API + worker.

    Design goals:
    - Very low overhead on hot paths (increment/set are non-blocking).
    - Best-effort operation; metrics must not break delivery flows.
    - Storage abstraction for in-memory or Redis backing.
    """

    def __init__(
        self,
        backend: MetricsBackend,
        counters: tuple[str, ...] = DEFAULT_COUNTERS,
        gauges: tuple[str, ...] = DEFAULT_GAUGES,
    ) -> None:
        self._backend = backend
        self._counter_names = list(counters)
        self._gauge_names = list(gauges)
        self._known = set(self._counter_names) | set(self._gauge_names)
        self._logger = logging.getLogger(__name__)
        self._unknown_logged: set[str] = set()

    def increment(self, name: str, amount: int = 1) -> None:
        if name not in self._known:
            self._log_unknown_metric(name)
            return
        try:
            self._backend.increment(name, amount=amount)
        except Exception as exc:
            self._logger.debug("metrics increment failed: %s", exc)

    def set_gauge(self, name: str, value: int) -> None:
        if name not in self._known:
            self._log_unknown_metric(name)
            return
        try:
            self._backend.set_gauge(name, value=value)
        except Exception as exc:
            self._logger.debug("metrics gauge set failed: %s", exc)

    async def snapshot(self) -> dict[str, int]:
        try:
            snap = await self._backend.snapshot(counters=self._counter_names, gauges=self._gauge_names)
        except Exception as exc:
            self._logger.debug("metrics snapshot failed: %s", exc)
            snap = MetricsSnapshot(
                counters={name: 0 for name in self._counter_names},
                gauges={name: 0 for name in self._gauge_names},
            )
        return snap.as_dict()

    def _log_unknown_metric(self, name: str) -> None:
        if name in self._unknown_logged:
            return
        self._unknown_logged.add(name)
        self._logger.warning("unknown metric name: %s", name)


def build_metrics_service(backend: str, redis_url: str, redis_namespace: str) -> MetricsService:
    backend_normalized = (backend or "memory").strip().lower()
    if backend_normalized == "redis":
        return MetricsService(
            backend=RedisMetricsBackend(redis=Redis.from_url(redis_url), namespace=redis_namespace),
        )
    return MetricsService(backend=InMemoryMetricsBackend())
