"""
dslighting.tools.dsflow.core.optimizer

DSFlow-style meta-optimizer (two-stage selection):
1) Coarse filter: stop a candidate after its first LLM call and score the plan.
2) Fine evaluation: run full workflow only for top-k candidates and grade via benchmark.

Key feature: the optimizer may propose NEW operators (as code) to extend its toolbox.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from dslighting.benchmark.core.base import BaseBenchmark
from dslighting.services.llm import LLMService
from dslighting.services.sandbox import SandboxService
from dslighting.services.workspace import WorkspaceService
from dslighting.state.operator_library import OperatorLibrary
from dslighting.state.search.experience import Experience
from dslighting.tools.dsflow.core.evaluation_helpers import EvaluationHelpers
from dslighting.tools.dsflow.core.operator_helpers import OperatorHelpers
from dslighting.tools.dsflow.core.task_helpers import TaskHelpers
from dslighting.tools.dsflow.operators import OperatorCatalog as _OperatorCatalog

logger = logging.getLogger(__name__)


class DSFlowWorkflowBase(OperatorHelpers, EvaluationHelpers, TaskHelpers):
    """
    A simplified DSFlow-style genetic optimizer with a two-stage evaluation:
    1) Coarse filter: stop after first LLM call and score the generated plan.
    2) Fine evaluation: run full workflow only for top candidates and grade with benchmark.

    This class is an optimizer (like AFlowWorkflow), not a BaseWorkflow.
    """

    def __init__(
        self,
        operators: Dict[str, Any],
        services: Dict[str, Any],
        agent_config: Dict[str, Any],
        benchmark: Optional[BaseBenchmark] = None,
    ):
        self.agent_config = agent_config
        self.dsflow_config = self._load_dsflow_config(agent_config)
        self.llm_service: LLMService = services["llm"]
        self.workspace: WorkspaceService = services["workspace"]
        self.sandbox_service: SandboxService = services["sandbox"]
        self.data_perception = services.get("data_perception")
        self.experience = Experience(self.workspace)
        self.benchmark = benchmark

        self.operator_catalog = _OperatorCatalog()
        self._builtin_operator_names: set[str] = set()
        self.operator_library: Optional[OperatorLibrary] = None
        self._library_versions: Dict[str, int] = {}
        if operators:
            # If caller provides operator instances, keep them as-is (legacy escape hatch).
            # DSFlow-style dynamic operator extension requires the internal catalog.
            self._external_operator_instances = operators
        else:
            self._external_operator_instances = None
            self._register_default_operators()

        if self._external_operator_instances is None and bool(
            getattr(self.dsflow_config, "operator_library_enabled", False)
        ):
            lib_path = Path(
                str(
                    getattr(
                        self.dsflow_config,
                        "operator_library_path",
                        "runs/dsflow_operator_library.json",
                    )
                )
            ).expanduser()
            if not lib_path.is_absolute():
                lib_path = Path.cwd() / lib_path
            self.operator_library = OperatorLibrary(lib_path)

        self.max_generations = int(self.dsflow_config.max_rounds)
        self.selected_candidates_count = int(self.dsflow_config.top_k_selection)
        self.population_size = max(3, self.selected_candidates_count + 1)

        # Incremental usage snapshots for coarse/fine score recording.
        self._last_usage_summary: Dict[str, Any] = self.llm_service.get_usage_summary()
        self._score_perf_start = time.perf_counter()
        self._last_score_perf = self._score_perf_start

    async def optimize(self) -> str:
        raise NotImplementedError(
            "Algorithm loop is implemented in `dslighting.workflows.search.dsflow_workflow.DSFlowWorkflow`."
        )

    def _auto_sync_custom_operators(self) -> None:
        """Keep source synchronization opt-in and package-safe.

        Discovered operators are persisted in ``OperatorLibrary``. DSLighting
        deliberately does not rewrite installed Python source at runtime.
        """
        if bool(getattr(self.dsflow_config, "auto_sync_custom_operators", False)):
            logger.warning(
                "DSFlow source auto-sync is unavailable in the packaged integration; "
                "operators remain persisted in %s.",
                getattr(self.dsflow_config, "operator_library_path", "the operator library"),
            )
