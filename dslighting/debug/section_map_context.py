"""Context variable for propagating data-perception section_map to debug observability.

The section_map (list[RenderedSectionSpan]) is computed during
DataPerceptionRuntime.analyze() / analyze_data() and needs to be carried
forward to the llm.request.prepared debug event where it is attached to the
request_messages PayloadRef.section_map_ref field.

Usage:
    from dslighting.debug.section_map_context import active_section_map, set_section_map

    # In DataPerceptionRuntime.analyze() — set before rendering:
    result = self._renderer.render_with_map(context, profile)
    set_section_map(result.section_map)
    try:
        return result.text
    finally:
        clear_section_map()

    # In _build_debug_event (observed_call.py) — read when storing request_messages:
    from dslighting.debug.section_map_context import active_section_map
    section_map = active_section_map.get()
"""

from contextvars import ContextVar
from typing import Any

# The section_map is list[RenderedSectionSpan] — basic serializable types.
active_section_map: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "active_section_map", default=None
)


def set_section_map(section_map: list[Any]) -> None:
    """Set the active section_map for the current async task."""
    active_section_map.set(section_map)


def clear_section_map() -> None:
    """Clear the active section_map (e.g., after rendering is complete)."""
    active_section_map.set(None)


def get_section_map() -> list[dict[str, Any]] | None:
    """Get the active section_map for the current async task, or None."""
    return active_section_map.get()
