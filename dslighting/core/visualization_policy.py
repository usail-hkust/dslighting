"""Shared visualization and display policy helpers.

This module centralizes the policy that governs whether agents may create
visual outputs and whether they may attempt interactive display.

Current policy model:
- ``allow``: plotting libraries and interactive display are allowed.
- ``no_display``: plotting libraries are allowed, but interactive display
  calls must be avoided. Code should save figures to disk instead.
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Any, Mapping, Optional


LEGACY_ENFORCE_NO_PLOTTING_KEY = "enforce_no_plotting"
VISUALIZATION_POLICY_KEY = "visualization_policy"


class VisualizationPolicy(str, Enum):
    """Execution-time visualization behavior."""

    ALLOW = "allow"
    NO_DISPLAY = "no_display"


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise ValueError(f"Unsupported boolean literal: {value}")


def coerce_visualization_policy(value: Any) -> VisualizationPolicy:
    """Normalize user input into a visualization policy enum."""

    if isinstance(value, VisualizationPolicy):
        return value

    normalized = str(value).strip().lower().replace("-", "_")
    if normalized in {"allow", "enabled"}:
        return VisualizationPolicy.ALLOW
    if normalized in {"no_display", "headless", "non_interactive"}:
        return VisualizationPolicy.NO_DISPLAY

    raise ValueError(
        f"Unsupported visualization policy: {value!r}. "
        "Expected one of: 'allow', 'no_display'."
    )


def legacy_no_plotting_to_policy(value: Any) -> VisualizationPolicy:
    """Convert the legacy bool alias to the new visualization policy."""

    return VisualizationPolicy.NO_DISPLAY if _coerce_bool(value) else VisualizationPolicy.ALLOW


def consume_visualization_policy(overrides: dict[str, Any]) -> Optional[VisualizationPolicy]:
    """Pop visualization policy overrides from a mutable mapping."""

    if VISUALIZATION_POLICY_KEY in overrides:
        policy = coerce_visualization_policy(overrides.pop(VISUALIZATION_POLICY_KEY))
        overrides.pop(LEGACY_ENFORCE_NO_PLOTTING_KEY, None)
        return policy
    if LEGACY_ENFORCE_NO_PLOTTING_KEY in overrides:
        return legacy_no_plotting_to_policy(overrides.pop(LEGACY_ENFORCE_NO_PLOTTING_KEY))
    return None


def resolve_visualization_policy_from_agent_config(
    agent_config: Mapping[str, Any] | None,
) -> VisualizationPolicy:
    """Resolve policy from agent config dictionaries or model dumps."""

    if not isinstance(agent_config, Mapping):
        return VisualizationPolicy.NO_DISPLAY

    visualization = agent_config.get("visualization")
    if isinstance(visualization, Mapping):
        policy = visualization.get("policy")
        if policy is not None:
            return coerce_visualization_policy(policy)

    # Backward compatibility for persisted configs that still carry the alias.
    for section_name in ("search", "autokaggle"):
        section = agent_config.get(section_name)
        if isinstance(section, Mapping) and LEGACY_ENFORCE_NO_PLOTTING_KEY in section:
            return legacy_no_plotting_to_policy(section[LEGACY_ENFORCE_NO_PLOTTING_KEY])

    return VisualizationPolicy.NO_DISPLAY


def resolve_visualization_policy_from_config(config: Any) -> VisualizationPolicy:
    """Resolve policy from a full DSLightingConfig-like object."""

    agent = getattr(config, "agent", None)
    if agent is None:
        return VisualizationPolicy.NO_DISPLAY

    visualization = getattr(agent, "visualization", None)
    if visualization is not None:
        policy = getattr(visualization, "policy", None)
        if policy is not None:
            return coerce_visualization_policy(policy)

    return resolve_visualization_policy_from_agent_config(
        agent.model_dump() if hasattr(agent, "model_dump") else None
    )


def should_force_noninteractive_backend(policy: VisualizationPolicy | str) -> bool:
    """Whether the sandbox should force a non-interactive plotting backend."""

    return coerce_visualization_policy(policy) == VisualizationPolicy.NO_DISPLAY


def build_visualization_instruction_text(policy: VisualizationPolicy | str) -> str:
    """Prompt guidance shared by all code-writing agents."""

    normalized = coerce_visualization_policy(policy)
    if normalized == VisualizationPolicy.ALLOW:
        return (
            "You may use plotting libraries when helpful. Prefer saving required "
            "outputs to files in the working directory."
        )

    return (
        "You may use plotting libraries such as matplotlib, seaborn, plotly, or "
        "library-specific plotting APIs when the task requires visual outputs. "
        "Do not use interactive display calls such as `matplotlib.pyplot.show()`, "
        "`pyplot.show()`, `Figure.show()`, `Image.show()`, or `cv2.imshow()`. "
        "Save figures directly to files and close them after saving."
    )


_DISPLAY_BLOCK_PATTERNS = [
    (re.compile(r"\bplt\.show\s*\("), "plt.show("),
    (re.compile(r"\bpyplot\.show\s*\("), "pyplot.show("),
    (re.compile(r"\bmatplotlib\.pyplot\.show\s*\("), "matplotlib.pyplot.show("),
    (re.compile(r"\b(?:fig|figure)\.show\s*\("), "figure.show("),
    (re.compile(r"\bImage\.show\s*\("), "Image.show("),
    (re.compile(r"\bcv2\.imshow\s*\("), "cv2.imshow("),
]


def find_blocked_display_usage(code: str, policy: VisualizationPolicy | str) -> list[str]:
    """Find interactive display calls that violate the policy."""

    if coerce_visualization_policy(policy) != VisualizationPolicy.NO_DISPLAY:
        return []

    blocked: list[str] = []
    for pattern, label in _DISPLAY_BLOCK_PATTERNS:
        if pattern.search(code):
            blocked.append(label)
    return blocked


def build_noninteractive_execution_preamble(policy: VisualizationPolicy | str) -> str:
    """Return a small preamble that forces headless plotting behavior."""

    if not should_force_noninteractive_backend(policy):
        return ""

    return (
        "import os\n"
        "os.environ.setdefault('MPLBACKEND', 'Agg')\n"
        "try:\n"
        "    import matplotlib\n"
        "    matplotlib.use('Agg')\n"
        "except Exception:\n"
        "    pass\n"
        "try:\n"
        "    import plotly.io as pio\n"
        "    pio.renderers.default = 'json'\n"
        "except Exception:\n"
        "    pass\n"
    )
