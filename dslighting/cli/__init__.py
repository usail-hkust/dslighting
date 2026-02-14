"""
DSLighting CLI modules.

Provides CLI utilities including progress management and shell completion.

Submodules:
- progress: Progress bar management for CLI operations
- completion: Shell completion scripts and utilities

Example usage:

    from dslighting.cli import ProgressManager
    from dslighting.cli.completion import install_completion

    with ProgressManager("Processing..."):
        # do work

    install_completion("bash")  # Install shell completion
"""

from dslighting.cli.progress import ProgressManager
from dslighting.cli.completion import (
    get_completion_script,
    install_completion,
    print_completion,
    get_argument_completions,
)

__all__ = [
    # Progress management
    "ProgressManager",
    # Shell completion
    "get_completion_script",
    "install_completion",
    "print_completion",
    "get_argument_completions",
]
