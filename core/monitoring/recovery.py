"""Error Recovery and Circuit Breakers for Payal AI.

Detects runtime anomalies, isolates failing integrations, and executes automated recovery strategies.
"""

from dataclasses import dataclass
import time
from typing import Any, Callable, Dict, Optional


@dataclass
class CircuitBreakerState:
    name: str
    failure_count: int = 0
    failure_threshold: int = 3
    cooldown_seconds: float = 30.0
    last_failure_time: float = 0.0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN


class CircuitBreakerManager:
    """Protects against cascading failures and automatically manages system recovery."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreakerState] = {}

    def get_breaker(
        self,
        name: str,
        threshold: int = 3,
        cooldown: float = 30.0,
    ) -> CircuitBreakerState:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreakerState(
                name=name,
                failure_threshold=threshold,
                cooldown_seconds=cooldown,
            )
        return self._breakers[name]

    def can_execute(self, name: str) -> bool:
        """Check if an operation on this resource is allowed or if circuit is open."""
        breaker = self.get_breaker(name)
        if breaker.state == "CLOSED":
            return True

        # Check if cooldown has elapsed to allow a test retry (HALF_OPEN)
        if time.time() - breaker.last_failure_time > breaker.cooldown_seconds:
            breaker.state = "HALF_OPEN"
            return True

        return False

    def record_success(self, name: str) -> None:
        """Reset breaker upon successful execution."""
        breaker = self.get_breaker(name)
        breaker.failure_count = 0
        breaker.state = "CLOSED"

    def record_failure(self, name: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Record an execution failure and trip circuit if threshold exceeded."""
        breaker = self.get_breaker(name)
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()

        if breaker.failure_count >= breaker.failure_threshold:
            breaker.state = "OPEN"

        return {
            "resource": name,
            "state": breaker.state,
            "failure_count": breaker.failure_count,
            "tripped": breaker.state == "OPEN",
            "cooldown_remaining": max(0.0, breaker.cooldown_seconds - (time.time() - breaker.last_failure_time)),
        }

    def list_status(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                "state": b.state,
                "failures": b.failure_count,
                "cooldown": b.cooldown_seconds,
                "can_execute": self.can_execute(name),
            }
            for name, b in self._breakers.items()
        }

    def reset_all(self) -> None:
        for b in self._breakers.values():
            b.failure_count = 0
            b.state = "CLOSED"


CIRCUIT_BREAKER = CircuitBreakerManager()
