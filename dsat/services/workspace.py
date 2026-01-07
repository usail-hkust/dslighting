"""
Service for managing the run-specific workspace, including data, logs, and artifacts.
"""
import logging
import shutil
import uuid
import os
import contextlib
from pathlib import Path
from typing import Dict, Optional

from dsat.common.constants import DEFAULT_WORKSPACE_DIR

logger = logging.getLogger(__name__)

class WorkspaceService:
    """
    Manages the file system for a single, isolated agent run.
    It creates a directory based on the provided unique run name and provides structured access to it.
    The responsibility for generating unique run names is delegated to the DSATRunner.
    """
    def __init__(self, run_name: str, base_dir: str = None):
        """
        Initializes the workspace for a new run.

        Args:
            run_name (str): A descriptive and unique name for the run, provided by the runner.
            base_dir (str, optional): The base directory where all run folders will be stored.
                                    If None, uses DEFAULT_WORKSPACE_DIR from constants.
        """
        
        # Use the constant if base_dir is not provided
        if base_dir is None:
            base_dir = DEFAULT_WORKSPACE_DIR
            
        if not Path(base_dir).is_absolute():
            # Use Path.cwd() as the base for relative paths
            base_dir_path = (Path.cwd() / base_dir).resolve()
        else:
            base_dir_path = Path(base_dir).resolve()

        base_dir_path.mkdir(parents=True, exist_ok=True)
            
        self.run_dir = base_dir_path / run_name
        self.sandbox_workdir = self.run_dir / "sandbox"

        self.paths: Dict[str, Path] = {
            "run_dir": self.run_dir,
            "sandbox_workdir": self.sandbox_workdir,
            "config": self.run_dir / "config.yaml",
            "workflow": self.run_dir / "workflow.py",
            "logs": self.run_dir / "logs",
            "state": self.run_dir / "state",
            "candidates": self.run_dir / "candidates",
            "artifacts": self.run_dir / "artifacts", 
            "results": self.run_dir / "results.json",
        }

        self._create_directories()
        logger.info(f"Workspace initialized at: {self.run_dir.resolve()}. Sandbox Workdir: {self.sandbox_workdir.resolve()}")

    def _create_directories(self):
        """Creates the full directory structure for the run."""
        for path in self.paths.values():
            if not path.suffix:  # Check if it's a directory
                path.mkdir(parents=True, exist_ok=True)

    def get_path(self, name: str) -> Path:
        """
        Retrieves a managed path from the workspace.

        Args:
            name (str): The key of the path to retrieve (e.g., 'logs', 'artifacts').

        Returns:
            Path: The absolute Path object for the requested resource.

        Raises:
            KeyError: If the requested path name is not defined.
        """
        if name == 'sandbox_cwd':
             logger.warning("Accessing deprecated 'sandbox_cwd'. Use 'sandbox_workdir' instead.")
             name = 'sandbox_workdir'

        if name not in self.paths:
            raise KeyError(f"Path '{name}' is not a defined workspace path.")
        return self.paths[name]

    def write_file(self, content: str, path_name: str, sub_path: str = None):
        """
        Writes content to a file within a managed directory.

        Args:
            content (str): The string content to write.
            path_name (str): The key of the managed directory (e.g., 'logs').
            sub_path (str, optional): A filename or relative path within the managed directory.
        """
        target_dir = self.get_path(path_name)
        file_path = target_dir / sub_path if sub_path else target_dir
        
        # Ensure parent directory of the file exists if sub_path contains folders
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug(f"Wrote {len(content)} bytes to {file_path}")

    def link_data_to_workspace(self, source_data_dir: Path):
        """
        Links or copies the CONTENTS of a source data directory into the run's sandbox_workdir.
        This ensures the agent runs in an isolated environment containing all inputs.
        """
        # Use sandbox_workdir as the destination
        destination_dir = self.get_path("sandbox_workdir")

        src = source_data_dir.resolve()
        if not src.exists() or not src.is_dir():
            raise FileNotFoundError(f"Source data directory not found: {src}")

        for item in src.iterdir():
            source_item = item
            destination_item = destination_dir / item.name

            # If the destination item already exists, skip it (idempotent behavior)
            if destination_item.exists() or destination_item.is_symlink():
                continue

            # Try to create a symlink for the item
            try:
                # Determine if the target is a directory for Windows compatibility
                target_is_directory = source_item.is_dir()
                os.symlink(source_item, destination_item, target_is_directory=target_is_directory)
                logger.debug(f"Linked {source_item.name} into sandbox.")
            
            except (OSError, NotImplementedError) as e:
                # Symlink not permitted. Fallback to copy.
                warning_message = (
                    f"Symlink creation failed for {item.name} ({e}). Falling back to copying. "
                )
                if os.name == 'nt':
                     warning_message += " On Windows, enable 'Developer Mode' or run as administrator for symlinks."
                
                logger.warning(warning_message)
                
                try:
                    if source_item.resolve() == destination_item.resolve():
                        logger.warning(
                            f"Skipping copy of {source_item.name} because source and destination "
                            "resolve to the same file. This may indicate a workspace configuration issue."
                        )
                        continue

                    if source_item.is_dir():
                        shutil.copytree(source_item, destination_item)
                    else:
                        shutil.copy2(source_item, destination_item)
                    logger.debug(f"Copied {source_item.name} into sandbox.")
                except Exception as copy_e:
                    logger.error(f"Failed to copy item {item.name}: {copy_e}", exc_info=True)
                    raise

        logger.info(f"Data from {src} successfully populated into {destination_dir}")

    def cleanup(self, keep_workspace: bool = False):
        """
        Removes the entire run directory unless explicitly told to keep it.
        """
        if keep_workspace:
            logger.info(f"Workspace preserved as requested: {self.run_dir.resolve()}")
            return

        logger.info(f"Cleaning up workspace: {self.run_dir.resolve()}")
        try:
            if self.run_dir.exists():
                shutil.rmtree(self.run_dir)
        except Exception as e:
            logger.error(f"Failed to clean up workspace {self.run_dir}: {e}")

