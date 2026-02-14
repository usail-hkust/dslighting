"""
Base configuration loader for benchmarks.

This module provides shared configuration loading logic used across
all benchmark implementations (MLE, ScienceBench, DABench).

Usage:
    from dslighting.benchmark.core.config_loader import BaseBenchmarkConfigLoader

    class MyBenchmark(BaseBenchmark):
        def __init__(self, ...):
            self.config_loader = BaseBenchmarkConfigLoader(
                config_key="my_benchmark_competitions"
            )
            self.config = self.config_loader.load_config()
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

logger = logging.getLogger(__name__)


class BaseBenchmarkConfigLoader:
    """
    Shared configuration loader for all benchmark types.

    Handles:
    - Loading config.yaml from framework directory
    - Extracting competition lists by key
    - Default values and error handling
    """

    def __init__(
        self,
        config_key: str = "competitions",
        config_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize config loader.

        Args:
            config_key: Key to look up in config file (e.g., "competitions",
                        "sciencebench_competitions")
            config_path: Explicit path to config.yaml. If None, uses default
                        framework location.
        """
        self.config_key = config_key
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()

    def _get_default_config_path(self) -> Path:
        """Get default config.yaml path in framework directory."""
        # Go up from benchmark/core/ to dslighting root
        framework_dir = Path(__file__).parent.parent.parent
        return framework_dir / "config.yaml"

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from config.yaml file.

        Returns:
            Dictionary with at least a "competitions" key.
        """
        try:
            if not self.config_path.exists():
                logger.warning(
                    f"Config file not found at {self.config_path}, "
                    "using default configuration"
                )
                return {"competitions": []}

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if not config:
                    return {"competitions": []}

                # Extract competitions using the configured key
                if self.config_key in config:
                    return {"competitions": list(config[self.config_key])}

                # Fallback to "competitions" key
                return {"competitions": list(config.get("competitions", []))}

        except Exception as e:
            logger.error(
                f"Error loading config file: {e}, using default configuration"
            )
            return {"competitions": []}

    def merge_competitions(
        self,
        config_competitions: List[Any],
        cli_competitions: Optional[List[Any]],
    ) -> List[Any]:
        """
        Merge config competitions with CLI-provided competitions.

        This handles both string (legacy) and dict (new) formats and
        preserves metadata from config when filtering by CLI args.

        Args:
            config_competitions: Competitions from config file
            cli_competitions: Competitions from CLI arguments (optional)

        Returns:
            Merged list of competition entries
        """
        if not cli_competitions:
            return config_competitions

        # Build index of config entries for metadata preservation
        config_map = {}
        for entry in config_competitions:
            if isinstance(entry, str):
                config_map[entry] = {"id": entry, "mode": "standard_ml"}
            elif isinstance(entry, dict) and "id" in entry:
                config_map[entry["id"]] = entry

        # Build merged list based on CLI args
        merged_list = []
        for cid in cli_competitions:
            comp_id = cid
            mode = "standard_ml"

            if isinstance(cid, dict):
                comp_id = cid.get("id")
                mode = cid.get("mode", "standard_ml")

            if comp_id in config_map:
                merged_list.append(config_map[comp_id])
            else:
                # New competition not in config
                merged_list.append(cid if isinstance(cid, str) else cid)

        return merged_list


def create_problem_entry(
    competition_id: str,
    mode: str = "standard_ml",
    **metadata
) -> Dict[str, Any]:
    """
    Create a standardized problem entry dictionary.

    Args:
        competition_id: Unique competition identifier
        mode: Task mode (standard_ml, code_generation, etc.)
        **metadata: Additional metadata

    Returns:
        Problem entry dictionary
    """
    entry = {"competition_id": competition_id}
    if mode != "standard_ml":
        entry["mode"] = mode
    entry.update(metadata)
    return entry
