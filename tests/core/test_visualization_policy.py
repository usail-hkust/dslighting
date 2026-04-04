from dslighting.core.visualization_policy import (
    VisualizationPolicy,
    build_noninteractive_execution_preamble,
    build_visualization_instruction_text,
    consume_visualization_policy,
    find_blocked_display_usage,
)


def test_consume_visualization_policy_prefers_explicit_policy() -> None:
    overrides = {"visualization_policy": "allow", "enforce_no_plotting": True}

    policy = consume_visualization_policy(overrides)

    assert policy == VisualizationPolicy.ALLOW
    assert overrides == {}


def test_find_blocked_display_usage_blocks_interactive_show_calls() -> None:
    code = "import matplotlib.pyplot as plt\nplt.plot([1, 2])\nplt.show()\n"

    blocked = find_blocked_display_usage(code, VisualizationPolicy.NO_DISPLAY)

    assert blocked == ["plt.show("]


def test_noninteractive_preamble_sets_headless_rendering() -> None:
    preamble = build_noninteractive_execution_preamble(VisualizationPolicy.NO_DISPLAY)

    assert "MPLBACKEND" in preamble
    assert "plotly.io" in preamble
    assert "matplotlib.use('Agg')" in preamble


def test_instruction_text_allows_plot_creation_but_forbids_display() -> None:
    text = build_visualization_instruction_text(VisualizationPolicy.NO_DISPLAY)

    assert "You may use plotting libraries" in text
    assert "Do not use interactive display calls" in text
