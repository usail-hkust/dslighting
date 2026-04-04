"""Shared validation helpers for ReAct runtime parameters."""

from __future__ import annotations


def validate_react_operator_params(
    *,
    obs_max_tokens: int,
    obs_head_tokens: int,
    obs_tail_tokens: int,
) -> None:
    """Validate observation truncation settings for the ReAct workflow."""
    if obs_max_tokens <= 0:
        raise ValueError("obs_max_tokens must be > 0")
    if obs_head_tokens <= 0:
        raise ValueError("obs_head_tokens must be > 0")
    if obs_tail_tokens <= 0:
        raise ValueError("obs_tail_tokens must be > 0")
    if obs_head_tokens + obs_tail_tokens > obs_max_tokens:
        raise ValueError(
            "obs_head_tokens + obs_tail_tokens must be <= obs_max_tokens"
        )


__all__ = ["validate_react_operator_params"]
