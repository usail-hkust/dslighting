"""
Conditional Operator - Branching Orchestration

Executes different operators based on conditions.
"""

from typing import Any, Dict, Callable


class Conditional:
    """
    Conditional orchestration - execute operators based on conditions.

    Example:
        conditional = Conditional(
            condition_fn=lambda ctx: "classification" in ctx.get("task", ""),
            true_op=classification_op,
            false_op=regression_op,
        )
        result = await conditional.execute(task="classification task")
    """

    def __init__(
        self,
        condition_fn: Callable[[Dict], bool],
        true_op: Any,
        false_op: Any = None
    ):
        """
        Initialize conditional execution.

        Args:
            condition_fn: Function that takes context and returns True/False
            true_op: Operator to execute if condition is True
            false_op: Operator to execute if condition is False (optional)
        """
        self.condition_fn = condition_fn
        self.true_op = true_op
        self.false_op = false_op

    async def execute(self, **kwargs) -> Any:
        """
        Execute conditionally based on condition function.

        Args:
            **kwargs: Input arguments (passed as context to condition_fn)

        Returns:
            Output from the executed operator
        """
        # Evaluate condition
        condition_result = self.condition_fn(kwargs)

        # Choose operator based on condition
        if condition_result:
            if self.true_op is None:
                return None
            return await self.true_op(**kwargs)
        else:
            if self.false_op is None:
                return None
            return await self.false_op(**kwargs)

    async def __call__(self, **kwargs) -> Any:
        """Allow conditional to be called like a function."""
        return await self.execute(**kwargs)
