"""Queue policy implementations for task scheduling."""

from __future__ import annotations

import logging
from collections import deque
from typing import TYPE_CHECKING, Any, Callable, Deque, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from dslighting.benchmark.core.scheduler_core import BenchmarkRuntimeScheduler

logger = logging.getLogger(__name__)


# Type alias for problem tuples
ProblemTuple = Tuple[int, Dict[str, Any]]


class BaseQueuePolicy:
    """Base class for queue scheduling policies."""

    def __init__(self, scheduler: "BenchmarkRuntimeScheduler"):
        self.scheduler = scheduler

    def order(self, problems: List[Dict[str, Any]]) -> List[ProblemTuple]:
        """Order problems according to the policy. Returns list of (index, problem) tuples."""
        raise NotImplementedError


class FIFOQueuePolicy(BaseQueuePolicy):
    """First-In-First-Out queue policy."""

    def order(self, problems: List[Dict[str, Any]]) -> List[ProblemTuple]:
        """Return problems in original order."""
        return [(idx, problem) for idx, problem in enumerate(problems, start=1)]


class LPTBackfillQueuePolicy(BaseQueuePolicy):
    """Longest Processing Time with backfill policy.

    High-priority and long tasks are scheduled first.
    """

    def order(self, problems: List[Dict[str, Any]]) -> List[ProblemTuple]:
        """Order problems by priority (descending), then by runtime (descending)."""
        weighted: List[Tuple[int, float, int, Dict[str, Any]]] = []
        for idx, problem in enumerate(problems, start=1):
            profile = self.scheduler.build_profile(problem, idx)
            weighted.append((profile.priority, profile.estimated_runtime_seconds, idx, problem))

        weighted.sort(key=lambda item: (-item[0], -item[1], item[2]))
        return [(idx, problem) for _, _, idx, problem in weighted]


class SRPTAgingBackfillQueuePolicy(BaseQueuePolicy):
    """Shortest Remaining Processing Time with aging and backfill.

    Prioritizes shorter tasks first to minimize average wait time.
    Aging is handled via stable index tie-break to avoid starvation.
    """

    def order(self, problems: List[Dict[str, Any]]) -> List[ProblemTuple]:
        """Order problems by priority (descending), then by runtime (ascending)."""
        weighted: List[Tuple[int, float, int, Dict[str, Any]]] = []
        for idx, problem in enumerate(problems, start=1):
            profile = self.scheduler.build_profile(problem, idx)
            weighted.append((profile.priority, profile.estimated_runtime_seconds, idx, problem))

        weighted.sort(key=lambda item: (-item[0], item[1], item[2]))
        return [(idx, problem) for _, _, idx, problem in weighted]


class MultilevelFeedbackQueuePolicy(BaseQueuePolicy):
    """Multi-level feedback queue scheduler.

    Tasks are categorized into three queues based on estimated runtime:
    - Short: < 30 seconds (highest priority)
    - Medium: 30-120 seconds
    - Long: > 120 seconds (lowest priority)

    Scheduler processes tasks in a 3:1 ratio (3 short tasks for every 1 medium/long task)
    to ensure short tasks complete quickly while preventing starvation of long tasks.
    """

    def order(self, problems: List[Dict[str, Any]]) -> List[ProblemTuple]:
        """Order problems using multi-level feedback queue."""
        enumerated = [(idx, problem) for idx, problem in enumerate(problems, start=1)]
        short_queue: Deque[ProblemTuple] = deque()
        medium_queue: Deque[ProblemTuple] = deque()
        long_queue: Deque[ProblemTuple] = deque()

        # Categorize tasks
        for idx, problem in enumerated:
            profile = self.scheduler.build_profile(problem, idx)
            runtime = profile.estimated_runtime_seconds

            if runtime < 30:
                short_queue.append((idx, problem))
            elif runtime < 120:
                medium_queue.append((idx, problem))
            else:
                long_queue.append((idx, problem))

        logger.info(
            "Multi-level feedback queue: short=%d, medium=%d, long=%d",
            len(short_queue),
            len(medium_queue),
            len(long_queue),
        )

        # Schedule with priority to short tasks
        result: List[ProblemTuple] = []
        round_robin_counter = 0

        while short_queue or medium_queue or long_queue:
            # Process 3 short tasks per round
            for _ in range(3):
                if short_queue:
                    result.append(short_queue.popleft())

            # Process 1 medium or long task per round
            if medium_queue:
                result.append(medium_queue.popleft())
            elif long_queue:
                result.append(long_queue.popleft())

            round_robin_counter += 1

            # Safety check: if we've done many rounds and short queue is empty,
            # drain the remaining queues to prevent starvation
            if round_robin_counter > 10 and not short_queue:
                while medium_queue:
                    result.append(medium_queue.popleft())
                while long_queue:
                    result.append(long_queue.popleft())
                break

        return result


# Policy registry
QUEUE_POLICY_REGISTRY: Dict[str, Callable[["BenchmarkRuntimeScheduler"], BaseQueuePolicy]] = {
    "fifo": FIFOQueuePolicy,
    "lpt_backfill": LPTBackfillQueuePolicy,
    "srpt_aging_backfill": SRPTAgingBackfillQueuePolicy,
    "multilevel_feedback": MultilevelFeedbackQueuePolicy,
}


def create_queue_policy(
    policy_name: str,
    scheduler: "BenchmarkRuntimeScheduler",
) -> BaseQueuePolicy:
    """Factory function to create a queue policy instance."""
    policy_cls = QUEUE_POLICY_REGISTRY.get(policy_name.lower(), FIFOQueuePolicy)
    return policy_cls(scheduler)


def get_queue_policy_names() -> List[str]:
    """Return list of available queue policy names."""
    return list(QUEUE_POLICY_REGISTRY.keys())
