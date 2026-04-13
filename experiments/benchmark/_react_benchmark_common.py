from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PROJECT_ROOT.parent
DEFAULT_LOCAL_DATA_ROOT = WORKSPACE_ROOT / "data"
DEFAULT_MODEL = "openai/deepseek-ai/DeepSeek-V3.1-Terminus"
DEFAULT_MAX_STEPS = 10
DEFAULT_TASK_TIMEOUT_SECONDS = 6 * 3600

BENCHMARK_ENV_VARS = {
    "dabench": "DSLIGHTING_DABENCH_DATA",
    "dacode": "DSLIGHTING_DACODE_DATA",
    "scienceagentbench": "DSLIGHTING_SCIENCEAGENTBENCH_DATA",
    "moscibench": "DSLIGHTING_MOSCIBENCH_DATA",
}

BENCHMARK_TYPE_ALIASES = {
    "scienceagentbench": "sciencebench",
}

DEFAULT_DATA_ROOTS = {
    "dabench": DEFAULT_LOCAL_DATA_ROOT / "dabench",
    "dacode": DEFAULT_LOCAL_DATA_ROOT / "dacode",
    "scienceagentbench": DEFAULT_LOCAL_DATA_ROOT / "scienceagentbench",
    "moscibench": DEFAULT_LOCAL_DATA_ROOT / "moscibench_local",
}


def _build_agent_runtime_config(benchmark_type: str, *, max_steps: int) -> dict:
    config = {"max_steps": max_steps}
    if benchmark_type == "moscibench":
        config.update(
            {
                "observation": {
                    "max_tokens": 32000,
                    "head_tokens": 16000,
                    "tail_tokens": 16000,
                    "max_chars": 120000,
                },
                "context": {
                    "max_history_chars": 240000,
                    "keep_recent_turns": 20,
                    "recent_observation_window": 12,
                    "summary_trigger_turns": 24,
                    "summary_max_chars": 12000,
                },
            }
        )
    return config


def _build_data_analysis_config(benchmark_type: str) -> dict:
    config = {"cache_enabled": False}
    if benchmark_type == "moscibench":
        config.update(
            {
                "profile": "full",
                "max_artifacts": 24,
                "max_report_chars": 80000,
            }
        )
    return config


def _build_output_contract_config(benchmark_type: str) -> dict:
    if benchmark_type != "moscibench":
        return {}
    return {
        "require_output_before_completion": True,
        "missing_output_feedback_retries": 2,
    }


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


def _str_env(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip()


def _resolve_env_file() -> Path | None:
    candidates = []
    explicit = os.getenv("DSLIGHTING_ENV_FILE")
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend(
        [
            PROJECT_ROOT / ".env",
            WORKSPACE_ROOT / "test_dslighting" / ".env",
        ]
    )
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved.exists():
            return resolved
    return None


def _resolve_data_root(benchmark_type: str) -> Path:
    env_name = BENCHMARK_ENV_VARS[benchmark_type]
    default = DEFAULT_DATA_ROOTS[benchmark_type]
    resolved = Path(os.getenv(env_name, str(default))).expanduser().resolve()
    if benchmark_type == "moscibench":
        competitions_root = resolved / "competitions"
        if competitions_root.exists() and not any(resolved.glob("mosci-*")):
            return competitions_root.resolve()
    return resolved


def _resolve_log_dir(benchmark_type: str) -> Path:
    explicit = os.getenv("BENCHMARK_LOG_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (
        PROJECT_ROOT / "experiments" / "benchmark" / "runs" / f"{benchmark_type}_react"
    ).resolve()


def run_react_benchmark(benchmark_type: str) -> int:
    env_file = _resolve_env_file()
    if env_file is not None:
        load_dotenv(env_file, override=True)

    repo_root = Path(os.getenv("DSLIGHTING_REPO", str(PROJECT_ROOT))).resolve()
    data_root = _resolve_data_root(benchmark_type)
    model = DEFAULT_MODEL
    max_steps = int(os.getenv("MAX_STEPS", str(DEFAULT_MAX_STEPS)))
    keep_workspace = _bool_env("KEEP_WORKSPACE", True)
    log_dir = _resolve_log_dir(benchmark_type)
    scheduler_policy = _str_env("SCHEDULER_POLICY", "balanced")
    max_concurrency = _int_env("MAX_CONCURRENCY", 8)
    llm_max_concurrency = _int_env("LLM_MAX_CONCURRENCY", 20)
    enable_task_rate_limiting = _bool_env("ENABLE_TASK_RATE_LIMITING", True)
    llm_task_start_rate = _float_env("LLM_TASK_START_RATE", 10.0)
    sandbox_task_start_rate = _float_env("SANDBOX_TASK_START_RATE", 20.0)
    task_rate_burst_factor = _float_env("TASK_RATE_BURST_FACTOR", 2.0)

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    if not data_root.exists():
        raise FileNotFoundError(f"{benchmark_type} data root not found: {data_root}")

    os.environ.setdefault(BENCHMARK_ENV_VARS[benchmark_type], str(data_root))
    resolved_benchmark_type = BENCHMARK_TYPE_ALIASES.get(benchmark_type, benchmark_type)

    print(f"Using repo: {repo_root}")
    print(f"Default local data root: {DEFAULT_LOCAL_DATA_ROOT}")
    print(f"Using data root: {data_root}")
    print(f"Benchmark type: {benchmark_type}")
    if resolved_benchmark_type != benchmark_type:
        print(f"Resolved benchmark type: {resolved_benchmark_type}")
    print("Workflow: react")
    print(f"Model: {model}")
    print(f"Max steps: {max_steps}")
    print(f"Keep workspace: {keep_workspace}")
    print(f"LLM_MODEL_CONFIGS set: {bool(os.environ.get('LLM_MODEL_CONFIGS'))}")
    print(f"Log dir: {log_dir}")
    print(f"Scheduler policy: {scheduler_policy}")
    print(f"Max concurrency: {max_concurrency}")
    print(f"LLM max concurrency: {llm_max_concurrency}")
    print(f"Enable task rate limiting: {enable_task_rate_limiting}")
    print(f"LLM task start rate: {llm_task_start_rate}")
    print(f"Sandbox task start rate: {sandbox_task_start_rate}")
    print(f"Task rate burst factor: {task_rate_burst_factor}")
    if env_file is not None:
        print(f"Loaded env file: {env_file}")

    from dslighting import configure_logging
    from dslighting.api.benchmark import DSBenchmark
    from dslighting.core.config.builder import ConfigBuilder

    configure_logging(
        level="INFO",
        trace_llm=_bool_env("DSLIGHTING_DEBUG", True),
        output_dir=str(log_dir / "debug_logs"),
        force=True,
    )

    config = ConfigBuilder().build_config(
        workflow="react",
        model=model,
        keep_workspace=keep_workspace,
        keep_workspace_on_failure=keep_workspace,
        data_analysis=_build_data_analysis_config(benchmark_type),
        agent_runtime=_build_agent_runtime_config(benchmark_type, max_steps=max_steps),
        output_contract=_build_output_contract_config(benchmark_type),
        run_name=f"{benchmark_type}_react_benchmark",
    )
    config.sandbox.timeout = DEFAULT_TASK_TIMEOUT_SECONDS
    config.run.dag_runtime.node_timeout_seconds = float(DEFAULT_TASK_TIMEOUT_SECONDS)

    config.scheduler.scheduler_policy = scheduler_policy
    config.scheduler.max_concurrency = max_concurrency
    config.scheduler.llm_max_concurrency = llm_max_concurrency
    config.scheduler.enable_task_rate_limiting = enable_task_rate_limiting
    config.scheduler.llm_task_start_rate = llm_task_start_rate
    config.scheduler.sandbox_task_start_rate = sandbox_task_start_rate
    config.scheduler.task_rate_burst_factor = task_rate_burst_factor

    benchmark = DSBenchmark(
        benchmark_type=resolved_benchmark_type,
        data_dir=str(data_root),
    )

    result = benchmark.run(
        config=config,
        log_path=str(log_dir),
        verbose=True,
    )

    print("\n=== Benchmark Result ===")
    print(f"type: {type(result).__name__}")
    for field in ["name", "results_path", "metadata_path"]:
        value = getattr(result, field, None)
        if value is not None:
            print(f"{field}: {value}")
    metadata = getattr(result, "metadata", None)
    if metadata is not None:
        print(f"metadata: {metadata}")
    results = getattr(result, "results", None)
    if results is not None:
        try:
            print(f"num_results: {len(results)}")
        except Exception:
            pass

    return 0
