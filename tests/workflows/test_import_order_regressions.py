from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import textwrap


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_benchmark_then_workflows_import_order_is_clean() -> None:
    result = _run_python(
        """
        from dslighting.api.benchmark import DSBenchmark
        from dslighting.core.config.builder import ConfigBuilder
        from dslighting.workflows import ReAct, ReActWorkflowFactory

        print(DSBenchmark.__name__)
        print(ConfigBuilder.__name__)
        print(ReAct.__name__)
        print(ReActWorkflowFactory.__name__)
        """
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined_output
    assert "partially initialized module" not in combined_output
    assert "Failed to import workflows module" not in combined_output


def test_react_preset_lookup_does_not_import_aflow() -> None:
    result = _run_python(
        """
        import sys

        from dslighting.workflows import ReAct

        print(ReAct.__name__)
        print("AFLOW_IMPORTED", "dslighting.workflows.search.aflow_workflow" in sys.modules)
        """
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined_output
    assert "AFLOW_IMPORTED False" in result.stdout


def test_factory_package_import_stays_lightweight() -> None:
    result = _run_python(
        """
        import sys

        import dslighting.workflows.factory as factory

        print("HAS_HELPER", hasattr(factory, "get_workflow_factory"))
        print("BUILTIN_IMPORTED", "dslighting.workflows.factory.builtin" in sys.modules)
        """
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined_output
    assert "BUILTIN_IMPORTED False" in result.stdout
