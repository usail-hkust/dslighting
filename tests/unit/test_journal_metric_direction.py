from __future__ import annotations

from dslighting.core.types import ReviewResult
from dslighting.state.search.journal import Node, maximize_from_lower_is_better


def test_maximize_from_lower_is_better_defaults_to_maximize_when_unknown() -> None:
    assert maximize_from_lower_is_better(True) is False
    assert maximize_from_lower_is_better(False) is True
    assert maximize_from_lower_is_better(None) is True


def test_node_absorb_review_prefers_task_context_direction() -> None:
    node = Node(plan="plan", code="print('hi')")
    review = ReviewResult(
        is_buggy=False,
        summary="looks good",
        metric_value=0.2,
        lower_is_better=None,
    )

    node.absorb_review(review, {"lower_is_better": True})

    assert node.metric.value == 0.2
    assert node.metric.maximize is False
