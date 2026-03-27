"""
Task handling utilities for DSLighting Agent.

This module contains functions for task creation and workflow determination.
Extracted from agent.py to improve code organization.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dslighting.core.types import TaskDefinition
from dslighting.core.data.context import TaskContext

logger = logging.getLogger(__name__)


def determine_workflow(config_workflow: Any, task_detection) -> str:
    """
    Determine which workflow to use for a task.

    Args:
        config_workflow: Workflow from configuration
        task_detection: Detected task information

    Returns:
        Workflow name (e.g., "aide", "autokaggle")
    """
    # If user specified workflow, use it
    if config_workflow and hasattr(config_workflow, 'name') and config_workflow.name:
        return config_workflow.name

    # Otherwise, use recommended workflow from detection
    if task_detection and hasattr(task_detection, 'recommended_workflow') and task_detection.recommended_workflow:
        return task_detection.recommended_workflow

    # Fallback to default
    return "aide"


def create_task_definition(
    loaded_data: TaskContext,
    task_id: Optional[str] = None,
    description: Optional[str] = None,
    output_path: Optional[str] = None,
    package_context: Optional[str] = None,
    **kwargs
) -> TaskDefinition:
    """
    Create TaskDefinition from TaskContext.

    Args:
        loaded_data: Loaded task context
        task_id: Optional task identifier
        description: Optional task description
        output_path: Optional output path
        package_context: Optional package context string
        **kwargs: Additional payload parameters

    Returns:
        TaskDefinition object
    """
    # Generate task ID if not provided
    if task_id is None:
        safe_name = str(uuid.uuid4())[:8]
        task_id = f"task_{safe_name}"

    # Get task type from loader and normalize to current TaskDefinition contract.
    detected_task_type = str(loaded_data.get_task_type() or "").strip().lower()
    valid_task_types = {"kaggle", "qa", "code", "datasci", "open_ended"}
    task_type = detected_task_type if detected_task_type in valid_task_types else "kaggle"

    # Get description
    if description is None:
        description = loaded_data.get_description()

    # Add package context to description if provided
    if package_context:
        try:
            description = f"{package_context}\n\nTask Description:\n{description}"
            logger.info("Package context added to task description")
        except Exception as e:
            logger.warning(f"Failed to add package context: {e}")

    # Get I/O instructions
    io_instructions = loaded_data.get_io_instructions() if hasattr(loaded_data, 'get_io_instructions') else None

    # Build payload
    payload = kwargs.copy()
    payload["description"] = description

    if io_instructions:
        payload["io_instructions"] = io_instructions

    data_dir = getattr(loaded_data, "data_dir", None)
    if data_dir:
        payload["data_dir"] = str(data_dir)

    resolved_output = output_path or f"submission_{task_id}.csv"
    payload["output_path"] = str(resolved_output)

    # Add canonical handler keys so runner task handlers can consume this
    # payload directly without legacy field assumptions.
    if task_type == "kaggle":
        if data_dir:
            payload["agent_visible_data_dir"] = str(data_dir)
            payload["public_data_dir"] = str(data_dir)
        payload["output_submission_path"] = str(resolved_output)
    elif task_type == "qa":
        payload.setdefault("question", description or "")
    elif task_type == "datasci":
        payload.setdefault("prompt", description or "")
        if data_dir:
            payload.setdefault("input_dir", str(data_dir))
        payload.setdefault("output_dir", str(Path(resolved_output).parent))
    elif task_type == "open_ended":
        if data_dir:
            payload.setdefault("raw_data_dir", str(data_dir))

    mode = getattr(getattr(loaded_data, "task_detection", None), "task_mode", None) or "standard_ml"
    if mode not in {"standard_ml", "open_ended"}:
        mode = "standard_ml"

    # Create task definition with the current schema
    task_def = TaskDefinition(
        task_id=task_id,
        task_type=task_type,
        mode=mode,
        payload=payload
    )

    logger.debug(f"Created task definition: {task_id} (type: {task_type})")
    return task_def
