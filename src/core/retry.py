"""Retry policies: fixed, exponential backoff, and jitter."""

from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RetryContext:
    """Context passed to a retry policy on each attempt."""

    attempt: int
    max_retries: int
    exception: Optional[Exception] = None
    elapsed: float = 0.0

    @property
    def should_retry(self) -> bool:
        return self.attempt < self.max_retries


class RetryPolicy(ABC):
    """Abstract base class for retry strategies."""

    @abstractmethod
    def delay_for(self, context: RetryContext) -> float:
        """Return the number of seconds to wait before the next retry."""
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the policy configuration."""
        ...


class FixedRetry(RetryPolicy):
    """Always waits the same number of seconds between retries."""

    def __init__(self, delay: float = 5.0, max_retries: int = 3) -> None:
        self.delay = delay
        self.max_retries = max_retries

    def delay_for(self, context: RetryContext) -> float:
        if not context.should_retry:
            return -1.0
        return self.delay

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "fixed", "delay": self.delay, "max_retries": self.max_retries}


class ExponentialRetry(RetryPolicy):
    """Doubles the delay on each subsequent retry."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 5,
    ) -> None:
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

    def delay_for(self, context: RetryContext) -> float:
        if not context.should_retry:
            return -1.0
        delay = self.base_delay * (2 ** context.attempt)
        return min(delay, self.max_delay)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "exponential",
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "max_retries": self.max_retries,
        }


class JitterRetry(RetryPolicy):
    """Exponential backoff with random jitter to prevent thundering herd."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter_factor: float = 0.5,
        max_retries: int = 5,
    ) -> None:
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor
        self.max_retries = max_retries

    def delay_for(self, context: RetryContext) -> float:
        if not context.should_retry:
            return -1.0
        base = self.base_delay * (2 ** context.attempt)
        jitter = random.uniform(0, self.jitter_factor * base)
        delay = base + jitter
        return min(delay, self.max_delay)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "jitter",
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "jitter_factor": self.jitter_factor,
            "max_retries": self.max_retries,
        }


class RetryManager:
    """Manages retry attempts for a single task execution."""

    def __init__(self, policy: RetryPolicy) -> None:
        self.policy = policy
        self._attempt = 0
        self._start_time = time.monotonic()

    @property
    def attempt(self) -> int:
        return self._attempt

    def should_continue(self) -> bool:
        return self._attempt < getattr(self.policy, "max_retries", 3)

    def next_delay(self, exc: Optional[Exception] = None) -> float:
        """Compute delay for the next retry and increment attempt counter."""
        ctx = RetryContext(
            attempt=self._attempt,
            max_retries=getattr(self.policy, "max_retries", 3),
            exception=exc,
            elapsed=time.monotonic() - self._start_time,
        )
        delay = self.policy.delay_for(ctx)
        self._attempt += 1
        return delay

    def reset(self) -> None:
        self._attempt = 0
        self._start_time = time.monotonic()