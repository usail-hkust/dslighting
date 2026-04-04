import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock


sys.modules.setdefault("pandas", Mock())

mock_utils = Mock()
mock_utils.get_logger = Mock(return_value=Mock())
mock_utils.import_fn = Mock()
sys.modules["dslighting.benchmark.vendor.mlebench.utils"] = mock_utils

fake_dslighting = types.ModuleType("dslighting")
fake_benchmark = types.ModuleType("dslighting.benchmark")
fake_grading = types.ModuleType("dslighting.benchmark.grading")
fake_errors = types.ModuleType("dslighting.benchmark.grading.errors")
fake_reporting = types.ModuleType("dslighting.benchmark.reporting")
fake_reporting_models = types.ModuleType("dslighting.benchmark.reporting.models")


class InvalidSubmissionError(Exception):
    pass


fake_errors.InvalidSubmissionError = InvalidSubmissionError
fake_reporting_models.CompetitionReport = object
sys.modules["dslighting"] = fake_dslighting
sys.modules["dslighting.benchmark"] = fake_benchmark
sys.modules["dslighting.benchmark.grading"] = fake_grading
sys.modules["dslighting.benchmark.grading.errors"] = fake_errors
sys.modules["dslighting.benchmark.reporting"] = fake_reporting
sys.modules["dslighting.benchmark.reporting.models"] = fake_reporting_models

spec = importlib.util.spec_from_file_location(
    "lazy_grade_helpers_under_test",
    Path(__file__).parent.parent.parent
    / "dslighting"
    / "benchmark"
    / "vendor"
    / "mlebench"
    / "grade_helpers.py",
)
grade_helpers = importlib.util.module_from_spec(spec)
sys.modules["lazy_grade_helpers_under_test"] = grade_helpers
spec.loader.exec_module(grade_helpers)

Grader = grade_helpers.Grader


def test_grader_defers_grade_fn_import_until_first_use():
    calls: list[str] = []

    def fake_import_fn(ref: str):
        calls.append(ref)

        def _grade(_submission, _answers):
            return 1.0

        return _grade

    grade_helpers.import_fn = fake_import_fn

    grader = Grader(name="StandardGrader", grade_fn="file:/tmp/grade.py:grade")

    assert calls == []

    first = grader.grade_fn
    second = grader.grade_fn

    assert calls == ["file:/tmp/grade.py:grade"]
    assert first is second
