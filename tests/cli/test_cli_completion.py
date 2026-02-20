from __future__ import annotations

from dslighting.cli.completion import get_argument_completions, get_completion_script


def test_argument_completions_include_parser_options() -> None:
    completions = get_argument_completions()
    assert "--all" in completions
    assert "--data-science-only" in completions
    assert "--version" in completions
    assert "--completions" in completions
    assert "--show-completion" in completions


def test_bash_completion_contains_dynamic_commands() -> None:
    script = get_completion_script("bash")
    assert "detect-packages" in script
    assert "version" in script


def test_zsh_completion_contains_dynamic_commands() -> None:
    script = get_completion_script("zsh")
    assert "detect-packages" in script
    assert "version" in script
