
import uuid
import contextlib
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Coroutine, Tuple
import time
from datetime import datetime, timezone
import shutil # Import shutil

from dslighting.state.search.experience import Experience
from dslighting.benchmark.evaluation.service import TaskEvaluationService
from dslighting.benchmark.evaluation.contract_builder import build_task_evaluation_contract
from dslighting.services.llm import LLMService
from dslighting.core.types import WorkflowCandidate
from dslighting.prompts.workflows.aflow import get_graph_optimize_prompt, GraphOptimize
from dslighting.workflows.templates.basic_kaggle_loop import get_initial_workflow_code
from dslighting.ops.presets import ScEnsembleOperator, AFlowReviewOperator, AFlowReviseOperator
from dslighting.utils.dynamic_import import import_workflow_from_string
from dslighting.benchmark.core.base import BaseBenchmark
from dslighting.error import DynamicImportError # Import DynamicImportError
from dslighting.benchmark.vendor.mlebench.utils import (
    get_module_dir,
    load_yaml,
)

logger = logging.getLogger(__name__)

class AFlowWorkflow:
    """
    AFlow workflow implements meta-optimization. It orchestrates an evolutionary
    search to find the best workflow for a given task, using a benchmark's
    validation set for fitness.
    
    This class is now a dedicated optimizer, not a BaseWorkflow.
    Its primary method is `optimize()`, which returns the best found workflow code.
    """
    
    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any], benchmark: Optional[BaseBenchmark] = None):
        # NOTE: It does not call super().__init__ as it's not a BaseWorkflow.
        self.llm_service: LLMService = services["llm"]
        self.workspace = services["workspace"]
        self.sandbox_service = services["sandbox"]
        self.data_perception = services.get("data_perception")
        self.experience = Experience(self.workspace)
        self.benchmark = benchmark
        
        self.aflow_operators = operators if operators else {
            "ScEnsemble": ScEnsembleOperator(llm_service=self.llm_service),
            "Review": AFlowReviewOperator(llm_service=self.llm_service),
            "Revise": AFlowReviseOperator(llm_service=self.llm_service)
        }
                
        optimizer_config = agent_config.get("optimizer", {})
        self.max_rounds = optimizer_config.get("max_rounds", 4)
        self.validation_runs_per_candidate = optimizer_config.get("validation_runs_per_candidate", 2) 
        self.top_k_selection = optimizer_config.get("top_k_selection", 3)

    def _resolve_competition_dir(self, competition_id: str) -> Path:
        """Resolve the competition directory without importing preparers."""
        benchmark_root = get_module_dir().parent
        dabench_root = benchmark_root / "dabench" / "competitions"
        sciencebench_root = benchmark_root / "sciencebench" / "competitions"
        mlebench_root = benchmark_root / "mlebench" / "competitions"

        if competition_id.startswith("sciencebench-") and (sciencebench_root / competition_id).exists():
            return sciencebench_root / competition_id
        if competition_id.startswith("dabench-") and (dabench_root / competition_id).exists():
            return dabench_root / competition_id
        if (dabench_root / competition_id).exists():
            return dabench_root / competition_id
        return mlebench_root / competition_id

    def _get_prepared_dirs(self, competition_id: str) -> tuple[Path, Path]:
        """
        Prefer prepared/public_val & prepared/private_val if they exist,
        otherwise fall back to prepared/public & prepared/private.
        This avoids any dependency on prepare.py/prepare_val.py.
        """
        base_data_dir = self.benchmark.registry.get_data_dir()  # type: ignore[union-attr]
        public_val = base_data_dir / competition_id / "prepared" / "public_val"
        private_val = base_data_dir / competition_id / "prepared" / "private_val"
        public = base_data_dir / competition_id / "prepared" / "public"
        private = base_data_dir / competition_id / "prepared" / "private"
        return (
            public_val if public_val.exists() else public,
            private_val if private_val.exists() else private,
        )

    def _load_competition_description(self, competition_id: str) -> str:
        """Load description from competition folder or config path."""
        comp_dir = self._resolve_competition_dir(competition_id)
        desc_path = comp_dir / "description.md"
        if desc_path.exists():
            return desc_path.read_text()
        config = load_yaml(comp_dir / "config.yaml")
        desc_path = get_module_dir().parent / config["description"]
        return desc_path.read_text()

    def _resolve_submission_contract_context(
        self,
        competition_id: str,
        output_path: Path,
    ) -> dict[str, Any]:
        comp_dir = self._resolve_competition_dir(competition_id)
        config = load_yaml(comp_dir / "config.yaml")
        evaluator_cfg = dict(config.get("evaluator") or {})
        submission_cfg = dict(evaluator_cfg.get("submission") or {})
        if not submission_cfg:
            return {
                "output_submission_path": str(output_path),
                "submission_filename": output_path.name,
                "submission_format": output_path.suffix.lower(),
            }

        data_root = self.benchmark.registry.get_data_dir()  # type: ignore[union-attr]
        entries_payload = []
        for entry in submission_cfg.get("entries") or ():
            if not isinstance(entry, dict):
                continue
            entry_payload = dict(entry)
            sample_value = str(entry_payload.get("sample") or "").strip()
            if sample_value:
                sample_path = Path(sample_value)
                if not sample_path.is_absolute():
                    sample_path = (data_root / sample_path).resolve()
                entry_payload["sample_path"] = str(sample_path)
            entry_payload.pop("sample", None)
            entries_payload.append(entry_payload)

        root_kind = str(submission_cfg.get("root_kind") or "file")
        contract_payload = {
            "output_submission_path": str(output_path),
            "submission_filename": output_path.name,
            "submission_format": output_path.suffix.lower(),
            "root_kind": root_kind,
            "entries": entries_payload,
        }
        return {
            "output_submission_path": str(output_path),
            "submission_filename": output_path.name,
            "submission_format": output_path.suffix.lower(),
            "submission_artifact_contract": contract_payload,
        }

    async def _grade_dabench_without_preparer(self, submission_path: Path, competition_id: str) -> float:
        """Grade a DABench submission using existing prepared answers and local grade.py."""
        competition = self.benchmark.registry.get_competition(competition_id)  # type: ignore[union-attr]
        contract, _ = build_task_evaluation_contract(
            competition=competition,
            source_id=getattr(getattr(self.benchmark.registry, "descriptor", None), "source_id", "mlebench"),  # type: ignore[union-attr]
            engine_id="mle",
            registry_root=self.benchmark.registry.get_competitions_dir(),  # type: ignore[union-attr]
            data_root=self.benchmark.registry.get_data_dir(),  # type: ignore[union-attr]
            mode="validation",
            output_submission_path=submission_path,
            evaluation_mode="artifact_submission",
        )
        outcome = await TaskEvaluationService().evaluate(
            submission_path=submission_path,
            contract=contract,
            mode="validation",
            metadata={"workflow": "aflow"},
        )
        return float(outcome.score) if outcome.score is not None else 0.0

    async def optimize(self) -> str:
        """
        Drives the entire meta-optimization process and returns the best workflow code.
        """
        meta_started_at = datetime.now(timezone.utc)
        meta_perf_start = time.perf_counter()
        usage_before = self.llm_service.get_usage_summary()
        best_workflow_code = ""

        if not self.benchmark or not hasattr(self.benchmark, 'set_mode') or not hasattr(self.benchmark, 'grade'):
            raise NotImplementedError(
                f"AFlow requires a compatible benchmark with `set_mode` and `grade` methods. "
                f"'{type(self.benchmark).__name__}' is not compatible."
            )
        
        if not self.benchmark.problems:
            raise ValueError(f"No problems found for benchmark '{self.benchmark.name}'. AFlow cannot proceed.")
        
        logger.info("AFlow starting meta-optimization...")
        
        # Set benchmark to 'validation' mode for the optimization phase.
        self.benchmark.set_mode('validation')
        logger.info("Benchmark set to 'validation' mode for optimization.")
        
        try:
            best_workflow_code = await self._run_optimization_loop()
            return best_workflow_code
        finally:
            meta_ended_at = datetime.now(timezone.utc)
            duration_seconds = round(time.perf_counter() - meta_perf_start, 4)
            usage_after = self.llm_service.get_usage_summary()
            meta_usage_delta = {
                "prompt_tokens": usage_after.get("prompt_tokens", 0) - usage_before.get("prompt_tokens", 0),
                "completion_tokens": usage_after.get("completion_tokens", 0) - usage_before.get("completion_tokens", 0),
                "total_tokens": usage_after.get("total_tokens", 0) - usage_before.get("total_tokens", 0),
                "total_cost": round(float(usage_after.get("total_cost", 0.0) - usage_before.get("total_cost", 0.0)), 12),
                "call_count": usage_after.get("call_count", 0) - usage_before.get("call_count", 0),
            }
            self.experience.record_score(
                -1,
                0.0,
                best_workflow_code or "",
                score_type="meta_summary",
                extra={
                    "started_at": meta_started_at.isoformat().replace("+00:00", "Z"),
                    "ended_at": meta_ended_at.isoformat().replace("+00:00", "Z"),
                    "duration_seconds": duration_seconds,
                    "usage_delta": meta_usage_delta,
                    "usage_total": usage_after,
                },
            )

    async def _run_optimization_loop(self) -> str:
        """Manages the evolutionary loop to find the best workflow."""
        initial_workflow_code = get_initial_workflow_code()
        
        # Get a representative problem to use for evaluation during optimization.
        # The original logic used only the first problem, we replicate that here.
        representative_problem = self.benchmark.problems[0]
        
        # We no longer generate a full data report here. The optimizer prompt will
        # now be more generic and focus on workflow logic, not specific filenames.
        # This prevents the optimizer from learning to hardcode "submission.csv".
        logger.info("Starting optimization loop without a pre-generated, instance-specific data report.")
        
        initial_fitness = await self._evaluate_workflow(initial_workflow_code, representative_problem)
        self.experience.record_score(0, initial_fitness, initial_workflow_code)
        logger.info(f"Initial workflow fitness: {initial_fitness:.4f}")
        
        best_workflow_code = initial_workflow_code
        best_fitness = initial_fitness
        
        for round_num in range(1, self.max_rounds):
            logger.info(f"--- AFlow Optimization Round {round_num}/{self.max_rounds-1} ---")
            parent_candidate = self.experience.select_parent_candidate(self.top_k_selection)
            if not parent_candidate:
                parent_candidate = WorkflowCandidate(
                    workflow_code=initial_workflow_code, 
                    fitness=initial_fitness,
                    round_num=0
                )
            
            try:
                optimized_code, modification = await self._optimize_workflow(
                    parent_candidate.workflow_code, 
                    parent_candidate.fitness or 0.0, 
                    parent_candidate.round_num
                )
                
                new_fitness = await self._evaluate_workflow(optimized_code, representative_problem)
                
                parent_round = parent_candidate.round_num if parent_candidate.round_num is not None else 0
                self.experience.record_score(round_num, new_fitness, optimized_code)
                self.experience.record_experience(parent_round, round_num, modification, parent_candidate.fitness or 0.0, new_fitness)
                
                logger.info(f"Round {round_num}: {modification} -> fitness: {new_fitness:.4f}")
                
                if new_fitness > best_fitness:
                    best_workflow_code = optimized_code
                    best_fitness = new_fitness
                    logger.info(f"New best workflow found with fitness: {best_fitness:.4f}")
            except Exception as e:
                logger.error(f"Error in optimization round {round_num}: {e}", exc_info=True)
        
        return best_workflow_code

    async def _optimize_workflow(self, parent_code: str, parent_score: float, parent_round_num: Optional[int]) -> tuple[str, str]:
        """Generates an optimized workflow using an LLM."""
        experience_str = self.experience.get_experience_summary(parent_round_num)
        
        optimize_prompt = get_graph_optimize_prompt(
            experience=experience_str, 
            score=parent_score, 
            graph_code=parent_code,
        )
        
        response = await self.llm_service.call_with_json(optimize_prompt, output_model=GraphOptimize)
        return response.graph, response.modification

    async def _evaluate_workflow(self, workflow_code: str, problem: Dict) -> float:
        """
        Evaluates a single candidate workflow on a single representative problem
        and returns its fitness score. This is the core fitness function.
        """
        scores = []
        
        # Get description and data_dir from the representative problem.
        # This assumes a Kaggle-like task handled by mle.py.
        competition_id = problem.get("competition_id")
        if not competition_id:
            raise ValueError("Representative problem for AFlow must have a 'competition_id'.")

        # Avoid registry.get_competition here to prevent importing prepare/prepare_val.
        raw_description = self._load_competition_description(competition_id)
        public_dir, _ = self._get_prepared_dirs(competition_id)
        data_dir = public_dir.absolute()

        # 1. Perform static analysis only ONCE.
        base_report = ""
        if self.data_perception is not None:
            base_report = self.data_perception.analyze_data(
                data_dir,
                task_type="kaggle",
                task_id=competition_id,
            )

        for i in range(self.validation_runs_per_candidate):
            unique_id = uuid.uuid4().hex[:6]
            submission_context = self._resolve_submission_contract_context(
                competition_id,
                output_path=Path(f"validation_submission_{i}_{unique_id}.csv"),
            )
            artifact_payload = submission_context.get("submission_artifact_contract")
            if isinstance(artifact_payload, dict) and str(artifact_payload.get("root_kind") or "file") == "directory":
                root_basename = "submission"
                config = load_yaml(self._resolve_competition_dir(competition_id) / "config.yaml")
                evaluator_cfg = dict(config.get("evaluator") or {})
                root_basename = (
                    str(((evaluator_cfg.get("submission") or {}).get("root_basename")) or "submission").strip()
                    or "submission"
                )
                temp_output_filename = f"{root_basename}_{i}_{unique_id}"
                submission_context = self._resolve_submission_contract_context(
                    competition_id,
                    output_path=Path(temp_output_filename),
                )
            else:
                temp_output_filename = f"validation_submission_{i}_{unique_id}.csv"
            temp_output_path = self.workspace.get_path("artifacts") / temp_output_filename

            try:
                if self.data_perception is not None:
                    io_instructions = self.data_perception.generate_io_instructions(
                        temp_output_path.name,
                        optimization_context=False,
                        submission_context=submission_context,
                    )
                else:
                    io_instructions = (
                        "All input data files are in the current working directory.\n"
                        f"Save the final submission artifact to `{temp_output_path.name}` in the current working directory."
                    )
                    
                # 3. Combine the raw description and cached base report. (IO instructions are passed separately now)
                description = f"{raw_description}\n{base_report}" if base_report else raw_description
                
                # 4. Setup the environment
                self.workspace.link_data_to_workspace(data_dir)


                # 5. Import the workflow, handling potential errors
                try:
                    workflow_class = import_workflow_from_string(workflow_code)
                except DynamicImportError as e:
                    logger.warning(f"Workflow evaluation run {i+1} failed due to invalid code: {e}")
                    scores.append(0.0)
                    continue

                # The dynamically created workflow requires these services.
                instance_services = {
                    "llm": self.llm_service,
                    "sandbox": self.sandbox_service,
                    "workspace": self.workspace
                }
                # It also needs a set of operators to choose from.
                instance = workflow_class(operators=self.aflow_operators, services=instance_services, agent_config={})
                
                await instance.solve(description, io_instructions, data_dir, temp_output_path)
                
                sandbox_workdir = self.workspace.get_path("sandbox_workdir")
                generated_file = sandbox_workdir / temp_output_path.name

                if generated_file.exists():
                    # ... (copy logic)
                    if generated_file.resolve() != temp_output_path.resolve():
                        if generated_file.is_dir():
                            if temp_output_path.exists():
                                if temp_output_path.is_dir():
                                    shutil.rmtree(temp_output_path)
                                else:
                                    temp_output_path.unlink()
                            shutil.copytree(generated_file, temp_output_path)
                        else:
                            shutil.copy(generated_file, temp_output_path)

                # Grade without depending on preparers for DABench tasks.
                if competition_id.startswith("dabench-"):
                    score = await self._grade_dabench_without_preparer(temp_output_path, competition_id)
                else:
                    score = await self.benchmark.grade(temp_output_path, competition_id=competition_id)
                scores.append(score)

            except Exception as e:
                logger.warning(f"Workflow evaluation run {i+1} failed: {e}", exc_info=False)
                scores.append(0.0)

            finally:
                if temp_output_path.exists():
                    with contextlib.suppress(OSError):
                        if temp_output_path.is_dir():
                            shutil.rmtree(temp_output_path)
                        else:
                            temp_output_path.unlink()
        return sum(scores) / len(scores) if scores else 0.0
    
