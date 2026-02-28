"""Circuit breaker para chamadas entre Wanda e agentes."""

from __future__ import annotations

import time
import json
from collections.abc import Awaitable, Callable

from wanda.resilience.errors import CircuitOpenError
from wanda.resilience.models import CircuitSnapshot, CircuitState


class CircuitBreaker:
    def __init__(
        self,
        agent_name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60,
        state_store=None,
        state_ttl_seconds: int = 3600,
        state_key_prefix: str = "wanda:circuit",
    ) -> None:
        self.agent_name = agent_name
        self.failure_threshold = max(1, failure_threshold)
        self.success_threshold = max(1, success_threshold)
        self.timeout_seconds = max(1, timeout_seconds)
        self._state_store = state_store
        self._state_ttl_seconds = max(60, state_ttl_seconds)
        self._state_key = f"{state_key_prefix}:{agent_name}:state"
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._successes = 0
        self._opened_at: float | None = None
        self._load_state()

    async def call(self, operation: Callable[[], Awaitable[object]]) -> object:
        self._load_state()
        self._refresh_half_open_if_needed()
        if self._state == CircuitState.OPEN:
            raise CircuitOpenError(f"Circuit OPEN para {self.agent_name}")
        try:
            result = await operation()
        except Exception:
            self._on_failure()
            raise
        self._on_success()
        return result

    def get_state(self) -> CircuitState:
        self._load_state()
        self._refresh_half_open_if_needed()
        return self._state

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._successes = 0
        self._opened_at = None
        self._persist_state()

    def snapshot(self) -> CircuitSnapshot:
        return CircuitSnapshot(
            agent_name=self.agent_name,
            state=self.get_state(),
            failures=self._failures,
            successes=self._successes,
        )

    def _on_failure(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._opened_at = time.time()
            self._successes = 0
            self._persist_state()
            return
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.time()
        self._persist_state()

    def _on_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._successes += 1
            if self._successes >= self.success_threshold:
                self.reset()
            else:
                self._persist_state()
            return
        self._failures = 0
        self._persist_state()

    def _refresh_half_open_if_needed(self) -> None:
        if self._state != CircuitState.OPEN or self._opened_at is None:
            return
        if (time.time() - self._opened_at) >= self.timeout_seconds:
            self._state = CircuitState.HALF_OPEN
            self._successes = 0
            self._persist_state()

    def _persist_state(self) -> None:
        if self._state_store is None:
            return
        payload = {
            "state": self._state.value,
            "failures": self._failures,
            "successes": self._successes,
            "opened_at": self._opened_at,
        }
        self._state_store.set(self._state_key, json.dumps(payload), ttl_seconds=self._state_ttl_seconds)

    def _load_state(self) -> None:
        if self._state_store is None:
            return
        raw = self._state_store.get(self._state_key)
        if not raw:
            return
        try:
            data = json.loads(raw)
            self._state = CircuitState(data.get("state", CircuitState.CLOSED.value))
            self._failures = int(data.get("failures", 0))
            self._successes = int(data.get("successes", 0))
            opened_at = data.get("opened_at")
            self._opened_at = float(opened_at) if opened_at is not None else None
        except Exception:
            self.reset()


class CircuitBreakerManager:
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60,
        state_store=None,
        state_ttl_seconds: int = 3600,
        state_key_prefix: str = "wanda:circuit",
    ) -> None:
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._timeout_seconds = timeout_seconds
        self._state_store = state_store
        self._state_ttl_seconds = state_ttl_seconds
        self._state_key_prefix = state_key_prefix
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, agent_name: str) -> CircuitBreaker:
        if agent_name not in self._breakers:
            self._breakers[agent_name] = CircuitBreaker(
                agent_name=agent_name,
                failure_threshold=self._failure_threshold,
                success_threshold=self._success_threshold,
                timeout_seconds=self._timeout_seconds,
                state_store=self._state_store,
                state_ttl_seconds=self._state_ttl_seconds,
                state_key_prefix=self._state_key_prefix,
            )
        return self._breakers[agent_name]

    def reset(self, agent_name: str) -> bool:
        breaker = self._breakers.get(agent_name)
        if breaker is None:
            return False
        breaker.reset()
        return True

    def snapshots(self) -> list[CircuitSnapshot]:
        return [breaker.snapshot() for breaker in self._breakers.values()]
