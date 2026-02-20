"""
Shell completion support for DSLighting CLI.

Provides shell completion scripts for bash and zsh.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Iterable

from dslighting.cli.__main__ import build_cli_parser

logger = logging.getLogger(__name__)


def _extract_parser_metadata() -> tuple[list[str], list[str]]:
    parser = build_cli_parser()
    global_opts: list[str] = []
    commands: list[str] = []
    subparsers_action = None

    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparsers_action = action
            continue
        global_opts.extend(action.option_strings)

    if subparsers_action is not None:
        commands.extend(sorted(subparsers_action.choices.keys()))
        for subparser in subparsers_action.choices.values():
            for action in subparser._actions:
                global_opts.extend(action.option_strings)

    # de-duplicate while preserving stable order
    seen: set[str] = set()
    deduped_opts: list[str] = []
    for item in global_opts:
        if item and item not in seen:
            seen.add(item)
            deduped_opts.append(item)

    return commands, deduped_opts


def _format_zsh_commands(commands: Iterable[str]) -> str:
    items = [f"        '{cmd}:{cmd}'" for cmd in commands]
    return "\n".join(items)


def _build_bash_completion(commands: list[str]) -> str:
    commands_str = " ".join(commands)
    return f"""# dslighting bash completion
_dslighting_completions()
{{
    local cur prev words cword
    _init_completion || return

    if [[ \"$cur\" == -* ]]; then
        COMPREPLY=($(compgen -W \"$(dslighting --completions bash 2>/dev/null)\" -- \"$cur\"))
        return
    fi

    local commands=\"{commands_str}\"
    COMPREPLY=($(compgen -W \"$commands\" -- \"$cur\"))
}}
complete -F _dslighting_completions dslighting
"""


def _build_zsh_completion(commands: list[str]) -> str:
    command_lines = _format_zsh_commands(commands)
    return f"""#compdef dslighting

_dslighting_completions() {{
    local -a commands
    commands=(
{command_lines}
    )

    if (( CURRENT == 2 )); then
        _describe -t commands 'dslighting commands' commands
        return
    fi
}}

compdef _dslighting_completions dslighting
"""


def get_completion_script(shell: str = "bash") -> str:
    """
    Get shell completion script for the specified shell.

    Args:
        shell: Shell type ("bash" or "zsh")

    Returns:
        Completion script string
    """
    commands, _ = _extract_parser_metadata()
    if shell.lower() == "bash":
        return _build_bash_completion(commands)
    elif shell.lower() == "zsh":
        return _build_zsh_completion(commands)
    else:
        raise ValueError(f"Unsupported shell: {shell}. Use 'bash' or 'zsh'.")


def install_completion(shell: str = "bash", user: bool = True) -> bool:
    """
    Install shell completion for dslighting.

    Args:
        shell: Shell type ("bash" or "zsh")
        user: Whether to install for current user (vs system-wide)

    Returns:
        True if installation was successful
    """
    script = get_completion_script(shell)
    shell_name = shell.lower()

    # Determine the completion file path based on shell and installation type
    if user:
        # User-level installation
        if shell_name == "bash":
            # For bash user-level, append to ~/.bash_completion
            comp_file = Path(os.path.expanduser("~/.bash_completion.d/dslighting"))
            comp_dir = comp_file.parent
        else:
            # For zsh user-level, use ~/.zsh/completion/_dslighting
            comp_file = Path(os.path.expanduser("~/.zsh/completion/_dslighting"))
            comp_dir = comp_file.parent
    else:
        # System-level installation
        if shell_name == "bash":
            # For bash system-level, use /etc/bash_completion.d/dslighting
            comp_dir = Path("/etc/bash_completion.d/")
            comp_file = comp_dir / "dslighting"
        else:
            # For zsh system-level, use /usr/local/share/zsh/site-functions/_dslighting
            comp_dir = Path("/usr/local/share/zsh/site-functions/")
            comp_file = comp_dir / "_dslighting"

    try:
        # Create the parent directory if it doesn't exist
        comp_dir.mkdir(parents=True, exist_ok=True)

        # Write the completion script to the file
        with open(comp_file, "w") as f:
            f.write(script)
        os.chmod(comp_file, 0o644)

        logger.info(f"Successfully installed {shell_name} completion to {comp_file}")
        return True
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to install completion script to {comp_file}: {e}")
        logger.error(f"Tip: Try running with 'sudo' for system-wide installation, or use --user flag")
        return False


def print_completion(shell: str = "bash") -> None:
    """
    Print shell completion script to stdout.

    Args:
        shell: Shell type ("bash" or "zsh")
    """
    print(get_completion_script(shell))


def get_argument_completions() -> str:
    """
    Get completions for command-line arguments.

    Returns:
        Space-separated list of completions
    """
    _, opts = _extract_parser_metadata()
    return " ".join(opts)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--completions":
        shell = sys.argv[2] if len(sys.argv) > 2 else "bash"
        if shell == "bash":
            print(get_argument_completions())
        else:
            print_completion(shell)
    else:
        # Print installation instructions
        print("DSLighting Shell Completion")
        print("=" * 40)
        print()
        print("To install bash completion:")
        print("  1. Add to ~/.bashrc:")
        print('     eval "$(dslighting --show-completion bash)"')
        print()
        print("To install zsh completion:")
        print("  1. Save completion to ~/.zsh/completion/dslighting")
        print("  2. Add to ~/.zshrc:")
        print('     fpath=(~/.zsh/completion $fpath)')
        print('     autoload compinit')
        print()
        print("Or run: dslighting --install-completion")
