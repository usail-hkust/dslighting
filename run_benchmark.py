# run_benchmark.py

import argparse
import asyncio
import logging
import multiprocessing
import os
import math
import sys
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Ensure relocated benchmark packages (mlebench/dabench) on sys.path.
# Allow importing benchmarks that live under this repo's benchmarks/ directory
# (modules are `benchmarks/mlebench`, `benchmarks/dabench`).
LOCAL_BENCHMARKS = Path(__file__).parent / "benchmarks"
if LOCAL_BENCHMARKS.exists():
    sys.path.insert(0, str(LOCAL_BENCHMARKS))

# Provide import aliases so legacy module strings like `mlebench.*` continue to work
# after moving packages under benchmarks/.
def _alias_module(old: str, new: str):
    if old in sys.modules:
        return
    try:
        mod = __import__(new, fromlist=["*"])
        sys.modules[old] = mod
    except ModuleNotFoundError:
        pass

_alias_module("mlebench", "benchmarks.mlebench")
_alias_module("mlebench.competitions", "benchmarks.mlebench.competitions")
_alias_module("dabench", "benchmarks.dabench")
_alias_module("dabench.competitions", "benchmarks.dabench.competitions")
_alias_module("sciencebench", "benchmarks.sciencebench")
_alias_module("sciencebench.competitions", "benchmarks.sciencebench.competitions")

from rich.console import Console, Group
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

# --- DSAT Core Component Imports ---
from dsat.config import DSATConfig, LLMConfig, WorkflowConfig, OptimizerConfig
from dsat.runner import DSATRunner, WORKFLOW_FACTORIES
from dsat.workflows.search.aflow_workflow import AFlowWorkflow

# --- Workflow factories ---
from dsat.workflows.factory import (
    AFlowWorkflowFactory,
    DynamicWorkflowFactory,
)

# --- Benchmark Class Imports ---
from dsat.benchmark.benchmark import BaseBenchmark
from dsat.benchmark.mle import MLEBenchmark
from dsat.benchmark.sciencebench import ScienceBenchBenchmark

# from benchmarks.humaneval import HumanEvalBenchmark # Future additions can be easily added

# load .env file
load_dotenv()

# --- Logging Setup ---
console = Console()
logging.basicConfig(
    level="INFO",
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
)
logger = logging.getLogger(__name__)


# Benchmark Registry
BENCHMARK_CLASSES = {
    "mle": MLEBenchmark,
    "dabench": MLEBenchmark,  # Alias for MLE with dabench naming
    "sciencebench": ScienceBenchBenchmark,
    # "datasci": DataSciBenchmark,  # Disabled: Not yet converted to mle-bench format
    # "humaneval": HumanEvalBenchmark,
}


def _get_env_setting(name: str, default=None):
    """Read an env var and strip quotes/whitespace."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().strip('"').strip("'")

def _load_model_configs() -> Dict[str, Dict[str, Any]]:
    """
    Load per-model overrides from env var `LLM_MODEL_CONFIGS`.

    Expected format (JSON object):
      {
        "<model_name>": {
          "api_key": "sk-..." | ["sk-1", "sk-2"],
          "api_base": "https://.../v1",
          "provider": "siliconflow",
          "temperature": 0.7
        }
      }
    """
    raw = _get_env_setting("LLM_MODEL_CONFIGS")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        logger.warning("Failed to parse LLM_MODEL_CONFIGS as JSON: %s", exc)
        return {}
    if not isinstance(parsed, dict):
        logger.warning("LLM_MODEL_CONFIGS must be a JSON object, got %s", type(parsed).__name__)
        return {}
    cleaned: Dict[str, Dict[str, Any]] = {}
    for k, v in parsed.items():
        if isinstance(k, str) and isinstance(v, dict):
            cleaned[k.strip()] = v
    return cleaned


def _normalize_model_dir_name(model_name: str) -> str:
    base_name = model_name.rsplit("/", 1)[-1]
    normalized = "".join(ch for ch in base_name if ch.isalnum() or ch in ("-", "_"))
    return normalized or "unknown-model"


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DSAT: A general-purpose agent evaluation framework.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--workflow",
        type=str,
        required=True,
        choices=WORKFLOW_FACTORIES.keys(),
        help="Agent workflow to run."
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        required=True,
        choices=BENCHMARK_CLASSES.keys(),
        help="Benchmark to execute."
    )
    parser.add_argument(
        "--dataset-file",
        type=str,
        required=False,
        default=None,
        help="Benchmark .jsonl path (optional, not used by MLE)."
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default="runs/benchmark_results",
        help="Directory for logs and artifacts."
    )
    parser.add_argument(
        "--keep-workspaces",
        action="store_true",
        help="Do not delete workspace directories after benchmark completion."
    )
    parser.add_argument(
        "--keep-workspace-on-failure",
        action="store_true",
        help="Keep workspace only when a task execution fails."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="[DABench/MLE/ScienceBench] Path to prepared competitions (alias for --mle-data-dir)."
    )
    parser.add_argument(
        "--mle-data-dir",
        type=str,
        default=None,
        help="[MLE only] Path to prepared competitions."
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="Override default LLM model."
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        default=None,
        help="Override LiteLLM provider alias (e.g. 'siliconflow')."
    )
    parser.add_argument(
        "--task-id",
        type=str,
        nargs="+",
        default=None,
        help="[DABench/MLE/ScienceBench] Override competition list (alias for --mle-competitions)."
    )
    parser.add_argument(
        "--mle-competitions",
        type=str,
        nargs="+",
        default=None,
        help="Override competition list for MLE."
    )
    parser.add_argument(
        "--best-workflow-path",
        type=str,
        default=None,
        help="[AFlow] Evaluate a saved best_workflow.py (skip Stage 1 meta-optimization).",
    )
    # DataSciBench arguments disabled (not yet converted to mle-bench format)
    # parser.add_argument(
    #     "--datasci-root-dir",
    #     type=str,
    #     default=None,
    #     help="[DataSciBench only] Path to DataSciBench root directory (contains 'data' and 'metric' folders). "
    #          "Example: E:/Desktop/nlp_alo_pre/liuhao/1/DataSciBench_Selected"
    # )
    # parser.add_argument(
    #     "--datasci-tasks",
    #     type=str,
    #     nargs="+",
    #     default=None,
    #     help="[DataSciBench only] Override task list."
    # )
    parser.add_argument(
        "--dsbench-data-dir",
        type=str,
        default=None,
        help="[DSBench only] Path to DSBench data."
    )
    parser.add_argument(
        "--dsbench-competitions",
        type=str,
        nargs="+",
        default=None,
        help="[DSBench only] Override competition list."
    )
    return parser.parse_args()


def _build_benchmark_summary(results_path: Optional[Path], run_records: List[Dict[str, Any]]):
    """
    Build a summary table from the CSV results and the runner's metadata records.
    """
    df = None
    if results_path and Path(results_path).exists():
        try:
            df = pd.read_csv(results_path)
        except Exception as exc:
            logger.warning("Failed to load benchmark results from %s: %s", results_path, exc)

    records_by_task = {record.get("task_id"): record for record in run_records if record.get("task_id")}
    table = Table(
        title="[bold]Per-Competition Results[/bold]",
        show_lines=True,
        expand=True,
    )
    table.add_column("Competition", style="cyan", no_wrap=True)
    table.add_column("Score", justify="right")
    table.add_column("Cost ($)", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Metadata", style="green")

    totals = {
        "count": 0,
        "success": 0,
        "cost": 0.0,
        "tokens": 0,
        "duration": 0.0,
        "score": 0.0,
        "score_count": 0,
    }
    rows_added = False
    seen_record_keys = set()
    cwd = Path.cwd()

    def is_nan(value: Any) -> bool:
        try:
            return math.isnan(float(value))
        except (TypeError, ValueError):
            return False

    def format_score(value: Any) -> str:
        if value is None or is_nan(value):
            return "—"
        try:
            return f"{float(value):.4f}"
        except (TypeError, ValueError):
            return "—"

    def format_cost(value: Any) -> str:
        if value is None or is_nan(value):
            return "—"
        try:
            return f"${float(value):.2f}"
        except (TypeError, ValueError):
            return "—"

    def format_tokens(value: Any) -> str:
        if value is None or is_nan(value):
            return "—"
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return "—"

    def format_duration(value: Any) -> str:
        if value is None or is_nan(value):
            return "—"
        try:
            return f"{float(value):.1f}s"
        except (TypeError, ValueError):
            return "—"

    def add_row(competition_id: str, score_val: Any, cost_val: Any, record: Optional[Dict[str, Any]]):
        nonlocal rows_added
        display_cost_val = cost_val
        if (display_cost_val is None or is_nan(display_cost_val)) and record:
            display_cost_val = record.get("summary", {}).get("total_cost")

        tokens_val = record.get("summary", {}).get("usage", {}).get("total_tokens") if record else None
        duration_val = record.get("timeline", {}).get("duration_seconds") if record else None
        success_flag = record.get("summary", {}).get("success") if record else None
        if success_flag is True:
            result_label = "✅ success"
        elif success_flag is False:
            result_label = "❌ failure"
        else:
            result_label = "—"

        metadata_path = record.get("metadata_path") if record else None
        if metadata_path:
            try:
                metadata_display = os.path.relpath(metadata_path, cwd)
            except Exception:
                metadata_display = metadata_path
        else:
            metadata_display = "—"

        table.add_row(
            competition_id or "N/A",
            format_score(score_val),
            format_cost(display_cost_val),
            format_tokens(tokens_val),
            format_duration(duration_val),
            result_label,
            metadata_display,
        )
        rows_added = True

        totals["count"] += 1
        if success_flag:
            totals["success"] += 1

        if display_cost_val is not None and not is_nan(display_cost_val):
            try:
                totals["cost"] += float(display_cost_val)
            except (TypeError, ValueError):
                pass

        if record:
            record_key = record.get("metadata_path") or record.get("task_id")
            if record_key:
                seen_record_keys.add(record_key)
            if tokens_val is not None and not is_nan(tokens_val):
                try:
                    totals["tokens"] += int(tokens_val)
                except (TypeError, ValueError):
                    pass
            if duration_val is not None and not is_nan(duration_val):
                try:
                    totals["duration"] += float(duration_val)
                except (TypeError, ValueError):
                    pass

        if score_val is not None and not is_nan(score_val):
            try:
                totals["score"] += float(score_val)
                totals["score_count"] += 1
            except (TypeError, ValueError):
                pass

    # Support both 'competition_id' (kaggle/mle) and 'task_id' (datasci) column names
    id_column = None
    if df is not None:
        if "competition_id" in df.columns:
            id_column = "competition_id"
        elif "task_id" in df.columns:
            id_column = "task_id"
    
    if df is not None and id_column is not None:
        for _, row in df.iterrows():
            comp_id = str(row.get(id_column, "")).strip() or "N/A"
            score_val = row.get("score")
            cost_val = row.get("cost")
            record = records_by_task.get(comp_id)
            add_row(comp_id, score_val, cost_val, record)

    for record in run_records:
        record_key = record.get("metadata_path") or record.get("task_id")
        if record_key in seen_record_keys:
            continue
        add_row(record.get("task_id", "N/A"), None, record.get("summary", {}).get("total_cost"), record)

    totals_table = None
    if rows_added:
        totals_table = Table.grid(padding=(0, 1))
        totals_table.add_column(style="bold cyan", justify="right")
        totals_table.add_column(justify="left")
        totals_table.add_row("Total tasks", str(totals["count"]))
        totals_table.add_row("Successful", str(totals["success"]))
        if totals["score_count"]:
            avg_score = totals["score"] / totals["score_count"]
            totals_table.add_row("Average score", format_score(avg_score))
        totals_table.add_row("Total cost", format_cost(totals["cost"]))
        totals_table.add_row("Total tokens", format_tokens(totals["tokens"]))
        totals_table.add_row("Total duration", format_duration(totals["duration"]))

    return (table if rows_added else None, totals_table)


async def main():
    """Main execution function."""
    args = parse_arguments()

    model_configs = _load_model_configs()
    llm_model = args.llm_model or _get_env_setting("LLM_MODEL")
    
    if not llm_model and model_configs:
        # Auto-select the first model from configs if no default is set
        llm_model = list(model_configs.keys())[0]
        logger.info(f"LLM_MODEL not set. Auto-selected first model from config: {llm_model}")
    
    if not llm_model:
        llm_model = "gpt-4o-mini" # Ultimate fallback

    base_model_name = _normalize_model_dir_name(llm_model)
    model_override = model_configs.get(llm_model, {})

    llm_provider = args.llm_provider or model_override.get("provider") or _get_env_setting("LLM_PROVIDER")
    llm_temperature = float(model_override.get("temperature") or _get_env_setting("LLM_TEMPERATURE", "0.7"))

    api_key_override = model_override.get("api_key")
    if isinstance(api_key_override, list):
        api_key = json.dumps(api_key_override)
    elif isinstance(api_key_override, str) and api_key_override.strip():
        api_key = api_key_override.strip()
    else:
        api_key = _get_env_setting("API_KEY", "EMPTY")

    api_base = str(model_override.get("api_base") or _get_env_setting("API_BASE", "https://api.openai.com/v1"))

    best_workflow_path = Path(args.best_workflow_path) if args.best_workflow_path else None
    is_meta_workflow = args.workflow == "aflow"
    is_best_mode = bool(best_workflow_path) and is_meta_workflow

    # --- 1. Create DSAT Agent Configuration ---
    try:
        config = DSATConfig(
            llm=LLMConfig(
                model=llm_model,
                temperature=llm_temperature,
                api_key=api_key,
                api_base=api_base,
                provider=llm_provider
            ),
            optimizer=OptimizerConfig()
        )
        config.workflow = WorkflowConfig(name=args.workflow)
        config.run.keep_all_workspaces = bool(args.keep_workspaces)
        config.run.keep_workspace_on_failure = bool(args.keep_workspace_on_failure)
        config.run.parameters = {
            "workflow": args.workflow,
            "benchmark": args.benchmark,
            "dataset_file": args.dataset_file,
            "log_path": args.log_path,
            "data_dir": args.data_dir,
            "mle_data_dir": args.mle_data_dir,
            "mle_competitions": args.mle_competitions,
            "task_id": args.task_id,
            "best_workflow_path": str(best_workflow_path) if best_workflow_path else None,
            "llm_model": llm_model,
            "llm_provider": llm_provider,
            "llm_temperature": llm_temperature,
            "api_base": api_base,
            "base_model": base_model_name,
        }
    except Exception as e:
        logger.error(f"Failed to create default DSATConfig: {e}", exc_info=True)
        return

    run_name = (
        f"{args.workflow}_best_on_{args.benchmark}"
        if is_best_mode
        else f"{args.workflow}_on_{args.benchmark}"
    )
    console.print(Panel(f"[bold]Agent Workflow:[/bold] {args.workflow}\n[bold]Benchmark:[/bold] {args.benchmark}", title="[bold cyan]DSAT Benchmark Run[/bold cyan]"))

    # --- 2. Instantiate DSAT Runner ---
    runner = DSATRunner(config)

    # --- 3. Prepare benchmark ---
    benchmark_class = BENCHMARK_CLASSES.get(args.benchmark)
    if not benchmark_class:
        logger.error(f"Benchmark '{args.benchmark}' not found in registry.")
        return

    log_dir = Path(args.log_path) / run_name / base_model_name
    log_dir.mkdir(parents=True, exist_ok=True)
    config.run.parameters["log_path"] = str(log_dir)

    benchmark_kwargs = {
        "name": args.benchmark,
        "file_path": args.dataset_file,
        "log_path": str(log_dir),
    }
    if args.benchmark in ("mle", "dabench", "sciencebench"):
        # Prefer new DABench aliases but keep legacy MLE flags for compatibility.
        data_dir = args.data_dir or args.mle_data_dir
        competitions = args.task_id or args.mle_competitions
        benchmark_kwargs["data_dir"] = data_dir
        if competitions:
            benchmark_kwargs["competitions"] = competitions
    # DataSciBench handling disabled (not yet converted to mle-bench format)
    # elif args.benchmark == "datasci":
    #     benchmark_kwargs["datasci_root_dir"] = args.datasci_root_dir
    #     if args.datasci_tasks:
    #         benchmark_kwargs["tasks"] = args.datasci_tasks
    elif args.benchmark == "dsbench":
        benchmark_kwargs["data_dir"] = args.dsbench_data_dir
        if args.dsbench_competitions:
            benchmark_kwargs["competitions"] = args.dsbench_competitions

    benchmark: BaseBenchmark = benchmark_class(**benchmark_kwargs)

    # --- 4. Execute workflow ---
    if is_meta_workflow:
        try:
            title = "[bold yellow]AFLOW[/bold yellow]"
            best_workflow_code: str

            if is_best_mode:
                console.print(Panel("Starting Stage 2: Final Evaluation on Test Set (best_workflow)", title=title))
                config.run.name = f"{run_name}_best_{uuid.uuid4().hex[:8]}"
                best_workflow_code = best_workflow_path.read_text()  # type: ignore[union-attr]
                (log_dir / "best_workflow.py").write_text(best_workflow_code)
            else:
                console.print(Panel("Starting Stage 1: Meta-Optimization", title=title))

                # Ensure meta-optimization uses a fresh workspace per run (avoid mixing Experience logs).
                config.run.name = f"{run_name}_opt_{uuid.uuid4().hex[:8]}"
                if config.workflow is not None:
                    config.workflow.params["workspace_base_dir"] = str(log_dir / "meta_optimization")

                optimizer_factory = AFlowWorkflowFactory()
                optimizer: AFlowWorkflow = optimizer_factory.create_workflow(config, benchmark=benchmark)

                best_workflow_code = await optimizer.optimize()
                (log_dir / "best_workflow.py").write_text(best_workflow_code)
                console.print("[green]✓ Meta-optimization complete. Best workflow code saved.[/green]")

                console.print(Panel("Starting Stage 2: Final Evaluation on Test Set", title=title))

            dynamic_factory = DynamicWorkflowFactory(code_string=best_workflow_code)

            final_run_config = config.model_copy(deep=True)
            final_run_config.workflow.name = args.workflow

            final_runner = DSATRunner(final_run_config)
            final_runner.register_workflow(args.workflow, dynamic_factory)
            final_runner.benchmark = benchmark

            if hasattr(benchmark, 'set_mode'):
                benchmark.set_mode('test')

            eval_function = final_runner.get_eval_function()
            await benchmark.run_evaluation(eval_fn=eval_function, model_name=llm_model)
            runner = final_runner

        except (NotImplementedError, ValueError) as e:
            logger.error(f"AFlow execution failed: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during AFlow execution: {e}", exc_info=True)
    else:
        runner.benchmark = benchmark
        eval_function = runner.get_eval_function()
        logger.info(f"Starting benchmark '{args.benchmark}' with workflow '{config.workflow.name}'...")
        await benchmark.run_evaluation(eval_fn=eval_function, model_name=llm_model)

    # --- 5. Present results ---
    summary_table, totals_table = _build_benchmark_summary(
        getattr(benchmark, "results_path", None),
        runner.get_run_records()
    )

    if summary_table:
        renderables = [summary_table]
        if totals_table:
            renderables.append(totals_table)
        console.print(
            Panel(
                Group(*renderables),
                title="[bold green]Benchmark Run Summary[/bold green]",
                subtitle=f"Logs saved in: [cyan]{log_dir.resolve()}[/cyan]"
            )
        )
    else:
        console.print(
            Panel(
                f"All evaluation outputs and logs are saved in:\n[cyan]{log_dir.resolve()}[/cyan]",
                title="[bold green]Benchmark Run Finished[/bold green]"
            )
        )

    # --- 6. Cleanup pending tasks ---
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for t in pending:
        t.cancel()
    await asyncio.gather(*pending, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
