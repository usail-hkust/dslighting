"""
Workflow utilities module.

This module contains common utility functions used across multiple workflow implementations.
"""

import logging
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

if TYPE_CHECKING:
    from dslighting.state.search.journal import Node
    from dslighting.state.context import ContextManager
    from dslighting.services.llm import LLMService

logger = logging.getLogger(__name__)


def build_error_history(
    node: Any,
    state: Any,
    context_manager: Any,
    max_depth: int = 3,
) -> str:
    """Traverses up a chain of buggy parent nodes to build a concise error history."""
    """
    Traverses up a chain of buggy parent nodes to build a concise error history.

    Args:
        node: The starting node (typically buggy) to build history from.
        state: The workflow state object that provides get_node method.
        context_manager: Context manager with summarize_error method.
        max_depth: Maximum depth to traverse up the parent chain.

    Returns:
        A formatted string containing the error history, or a message if no history found.
    """
    history = []
    current = node
    depth = 0
    while current and getattr(current, "is_buggy", False) and depth < max_depth:
        error_summary = context_manager.summarize_error(
            getattr(current, "term_out", ""), getattr(current, "exc_type", None)
        )
        entry = (
            f"--- Failure at Step #{getattr(current, 'step', '?')} ---\n"
            f"Plan: {getattr(current, 'plan', 'N/A')}\n"
            f"Code:\n```python\n{getattr(current, 'code', '')}\n```\n"
            f"Error:\n```\n{error_summary}\n```"
        )
        history.append(entry)
        depth += 1
        parent_id = getattr(current, "parent_id", None)
        if parent_id:
            current = state.get_node(parent_id) if hasattr(state, "get_node") else None
        else:
            current = None

    if not history:
        return "No error history found."

    # Reverse to show chronological order (oldest failure first)
    return "\n".join(reversed(history))


def capture_llm_history(
    llm_service: "LLMService",
    start_index: int = 0,
) -> List[Dict[str, Any]]:
    """
    Capture LLM call history from a given start index.

    Args:
        llm_service: The LLM service object with get_call_history method.
        start_index: The starting index in the history. If 0, returns all history.
                     Use the result of llm_history_length() before calls to get new calls only.

    Returns:
        List of LLM call history entries from start_index to the end.
    """
    if not hasattr(llm_service, "get_call_history"):
        return []

    history = llm_service.get_call_history()
    if start_index <= 0:
        return list(history)
    if start_index < len(history):
        return history[start_index:]
    return []


def llm_history_length(llm_service: "LLMService") -> int:
    """
    Get the current length of LLM call history.

    Args:
        llm_service: The LLM service object with get_call_history method.

    Returns:
        The number of calls in the history, or 0 if unavailable.
    """
    if not hasattr(llm_service, "get_call_history"):
        return 0
    return len(llm_service.get_call_history())


# Output file collection utilities

# Common output file extensions to look for
OUTPUT_EXTENSIONS: Set[str] = {
    ".csv", ".txt", ".json", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".pdf",
    ".html", ".py", ".pkl", ".pickle", ".npy", ".npz", ".h5", ".hdf5", ".parquet"
}

# Files to ignore when scanning for outputs
IGNORE_FILES: Set[str] = {"prompt.json", ".gitkeep", ".DS_Store", "thumbs.db"}


def extract_output_filenames_from_description(description: str) -> List[str]:
    """
    Extract all potential output filenames from task description.

    Args:
        description: The task description text to search for output file patterns.

    Returns:
        A list of filenames (without path) that might be expected outputs.
    """
    filenames = []

    # Patterns to match various ways output files are specified
    patterns = [
        # "saved in/to 'filename.ext'" or "saved in/to \"filename.ext\""
        r"saved?\s+(?:in|to|as)\s+[\"']([^\"']+\.\w+)[\"']",
        # "output file named 'filename.ext'"
        r"output\s+file\s+(?:named|called)?\s*[\"']([^\"']+\.\w+)[\"']",
        # "save the results/output to 'filename.ext'"
        r"save\s+(?:the\s+)?(?:results?|output|data|file)\s+(?:to|in|as)\s+[\"']([^\"']+\.\w+)[\"']",
        # "results should be saved in 'filename.ext'"
        r"(?:results?|output)\s+should\s+be\s+saved\s+(?:in|to|as)\s+[\"']([^\"']+\.\w+)[\"']",
        # "write to 'filename.ext'"
        r"write\s+(?:to|into)\s+[\"']([^\"']+\.\w+)[\"']",
        # "export to 'filename.ext'"
        r"export\s+(?:to|as)\s+[\"']([^\"']+\.\w+)[\"']",
        # "filename.csv" or 'filename.csv' standalone in quotes (common patterns)
        r"[\"']([a-zA-Z0-9_\-]+\.(?:csv|txt|json|xlsx|png|jpg|pdf|html|py))[\"']",
    ]

    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, description, re.IGNORECASE):
            filename = match.group(1)
            # Clean up the filename
            filename = filename.strip()
            # Only add if it looks like a valid filename and not seen before
            if filename and "/" not in filename and "\\" not in filename and filename not in seen:
                filenames.append(filename)
                seen.add(filename)

    return filenames


def get_initial_sandbox_files(sandbox_workdir: Path) -> Set[str]:
    """
    Get the set of files initially present in sandbox (to detect new files later).

    Args:
        sandbox_workdir: Path to the sandbox work directory.

    Returns:
        A set of file names initially present in the sandbox.
    """
    if not sandbox_workdir.exists():
        return set()
    return {f.name for f in sandbox_workdir.iterdir() if f.is_file()}


def find_new_output_files(
    sandbox_workdir: Path,
    initial_files: Set[str],
    output_extensions: Optional[Set[str]] = None,
    ignore_files: Optional[Set[str]] = None,
) -> List[Path]:
    """
    Find all new files created in sandbox since initial state.

    Args:
        sandbox_workdir: Path to the sandbox work directory.
        initial_files: Set of file names that were present initially.
        output_extensions: Set of file extensions to consider as output files.
                           Defaults to OUTPUT_EXTENSIONS.
        ignore_files: Set of file names to ignore. Defaults to IGNORE_FILES.

    Returns:
        A list of Path objects for new output files.
    """
    if output_extensions is None:
        output_extensions = OUTPUT_EXTENSIONS
    if ignore_files is None:
        ignore_files = IGNORE_FILES

    new_files = []
    if not sandbox_workdir.exists():
        return new_files

    for f in sandbox_workdir.iterdir():
        if not f.is_file():
            continue
        if f.name in initial_files:
            continue
        if f.name.lower() in ignore_files:
            continue
        if f.name.startswith("_sandbox_script_"):
            continue
        # Check if it's a recognized output type
        if f.suffix.lower() in output_extensions or f.suffix == "":
            new_files.append(f)

    return new_files


def collect_output_files(
    sandbox_workdir: Path,
    output_path: Path,
    expected_filenames: List[str],
    initial_files: Set[str],
    output_extensions: Optional[Set[str]] = None,
    ignore_files: Optional[Set[str]] = None,
) -> bool:
    """
    Collect output files from sandbox to destination directory.

    Strategy:
    1. First, check if the expected output file (output_path.name) exists
    2. Then, check for any files matching expected_filenames from task description
    3. Finally, collect any new files created during execution

    All matching files are copied to output_path.parent, preserving original names.
    The primary output is also copied to output_path for compatibility.

    Args:
        sandbox_workdir: Path to the sandbox work directory.
        output_path: The primary output path for the workflow.
        expected_filenames: List of filenames expected from task description.
        initial_files: Set of file names present initially in sandbox.
        output_extensions: Set of file extensions to consider as output files.
        ignore_files: Set of file names to ignore.

    Returns:
        True if at least one output file was collected.
    """
    if output_extensions is None:
        output_extensions = OUTPUT_EXTENSIONS
    if ignore_files is None:
        ignore_files = IGNORE_FILES

    output_path.parent.mkdir(parents=True, exist_ok=True)
    collected = False
    copied_files: Set[str] = set()
    default_output = sandbox_workdir / output_path.name
    directory_mode = default_output.is_dir() or (not output_path.suffix and any(
        (sandbox_workdir / filename).exists() for filename in expected_filenames
    ))

    def _replace_path(src: Path, dst: Path) -> None:
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)

    def _copy_into_collection_root(src: Path, name: str) -> Path:
        if directory_mode:
            output_path.mkdir(parents=True, exist_ok=True)
            dst = output_path / name
        else:
            dst = output_path.parent / name
        _replace_path(src, dst)
        return dst

    # 1. Check for the default expected output file
    if default_output.exists():
        _replace_path(default_output, output_path)
        copied_files.add(output_path.name)
        collected = True
        logger.info(
            "Copied default output %s to %s",
            "directory" if default_output.is_dir() else "file",
            output_path,
        )

    # 2. Check for files specified in task description
    for filename in expected_filenames:
        src_file = sandbox_workdir / filename
        if src_file.exists() and filename not in copied_files:
            dst_file = _copy_into_collection_root(src_file, filename)
            copied_files.add(filename)
            collected = True
            logger.info("Copied expected output file '%s' to %s", filename, dst_file)

            # If no default output was found, also copy first expected file as the default
            if not output_path.exists() and not directory_mode:
                _replace_path(src_file, output_path)
                logger.info("Also copied '%s' as default output to %s", filename, output_path)

    # 3. Collect any other new files created during execution
    new_files = find_new_output_files(
        sandbox_workdir, initial_files, output_extensions, ignore_files
    )
    for src_file in new_files:
        if src_file.name not in copied_files:
            dst_file = _copy_into_collection_root(src_file, src_file.name)
            copied_files.add(src_file.name)
            collected = True
            logger.info("Copied new output file '%s' to %s", src_file.name, dst_file)

            # If still no default output, use first new file
            if not output_path.exists() and not directory_mode:
                _replace_path(src_file, output_path)
                logger.info("Also copied '%s' as default output to %s", src_file.name, output_path)

    if collected:
        logger.info(
            "Total %d output file(s) collected to %s", len(copied_files), output_path.parent
        )

    return collected
