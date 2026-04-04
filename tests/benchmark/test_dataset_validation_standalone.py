"""
Test suite for dataset deep validation functionality in is_dataset_prepared().

This is a standalone test that mocks dependencies to avoid import issues.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from unittest.mock import Mock, patch, MagicMock

import pytest
import pandas as pd


# Mock the dependencies before importing
sys.modules['diskcache'] = Mock()
sys.modules['yaml'] = Mock()
sys.modules['tenacity'] = Mock()
sys.modules['tqdm'] = Mock()
sys.modules['tqdm.auto'] = Mock()
sys.modules['appdirs'] = Mock()

# Mock utility functions
mock_utils = Mock()
mock_utils.get_logger = Mock(return_value=Mock())
mock_utils.authenticate_kaggle_api = Mock()
mock_utils.extract = Mock()
mock_utils.get_diff = Mock()
mock_utils.is_empty = lambda path: not any(path.iterdir()) if path.exists() and path.is_dir() else True
mock_utils.load_yaml = Mock()
mock_utils.get_path_to_callable = Mock(return_value="test")
sys.modules['dslighting.benchmark.vendor.mlebench.utils'] = mock_utils
sys.modules['dslighting.benchmark.vendor.mlebench.registry'] = Mock()

# Now we can import the data module functions directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "mlebench_data",
    Path(__file__).resolve().parents[2]
    / "dslighting"
    / "benchmark"
    / "vendor"
    / "mlebench"
    / "data.py"
)
mlebench_data = importlib.util.module_from_spec(spec)
sys.modules['mlebench_data'] = mlebench_data

# Mock pandas before loading
with patch('pandas.DataFrame', pd.DataFrame):
    with patch('pandas.read_csv', pd.read_csv):
        spec.loader.exec_module(mlebench_data)

is_dataset_prepared = mlebench_data.is_dataset_prepared


@dataclass
class MockCompetition:
    """Mock competition object for testing."""
    public_dir: Path
    private_dir: Path
    answers: Path
    sample_submission: Path
    evaluator_config: dict | None = None


class TestDatasetPreparedBasic:
    """Test basic functionality of is_dataset_prepared (backward compatibility)."""

    def test_missing_required_attributes(self):
        """Test that missing required attributes raises TypeError."""
        competition = MockCompetition(
            public_dir=Path("/tmp/public"),
            private_dir=Path("/tmp/private"),
            answers=Path("/tmp/answers.csv"),
            sample_submission=Path("/tmp/sample.csv"),
        )
        # Remove one attribute to test error handling
        delattr(competition, 'public_dir')

        with pytest.raises(TypeError, match="Expected a competition-like object"):
            is_dataset_prepared(competition)

    def test_nonexistent_public_directory(self, tmp_path):
        """Test that nonexistent public directory returns False."""
        competition = MockCompetition(
            public_dir=tmp_path / "nonexistent_public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "answers.csv",
            sample_submission=tmp_path / "sample.csv",
        )
        # Create private directory and files
        (tmp_path / "private").mkdir()
        (tmp_path / "answers.csv").touch()
        (tmp_path / "sample.csv").touch()

        assert is_dataset_prepared(competition) is False

    def test_empty_public_directory(self, tmp_path):
        """Test that empty public directory returns False."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "answers.csv",
            sample_submission=tmp_path / "sample.csv",
        )
        # Create directories
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()
        (tmp_path / "answers.csv").touch()
        (tmp_path / "sample.csv").touch()

        assert is_dataset_prepared(competition) is False

    def test_grading_only_mode(self, tmp_path):
        """Test grading_only mode skips public directory checks."""
        competition = MockCompetition(
            public_dir=tmp_path / "nonexistent_public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "answers.csv",
            sample_submission=tmp_path / "sample.csv",
        )
        # Create private directory and answers, but not public
        (tmp_path / "private").mkdir()
        (tmp_path / "answers.csv").write_text("data")  # Write some content so it's not empty
        (tmp_path / "private" / "test.txt").write_text("test")  # Make private dir non-empty

        # grading_only should succeed without public directory
        assert is_dataset_prepared(competition, grading_only=True) is True


class TestDatasetDeepValidation:
    """Test deep validation functionality."""

    def test_deep_validation_missing_description(self, tmp_path):
        """Test that deep validation fails when description.md is missing."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/sample.csv",
        )

        # Create directories and files
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()

        # Create CSV files but no description.md
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        df.to_csv(tmp_path / "private/answers.csv", index=False)
        df.to_csv(tmp_path / "public/sample.csv", index=False)

        assert is_dataset_prepared(competition) is True
        assert is_dataset_prepared(competition, deep=True) is False

    def test_deep_validation_with_description(self, tmp_path):
        """Test that deep validation passes with description.md present."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/sample.csv",
        )

        # Create directories and files
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()

        # Create CSV files
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        df.to_csv(tmp_path / "private/answers.csv", index=False)
        df.to_csv(tmp_path / "public/sample.csv", index=False)

        # Create description.md
        (tmp_path / "public/description.md").write_text("Test description")

        assert is_dataset_prepared(competition, deep=True) is True

    def test_deep_validation_empty_csv(self, tmp_path):
        """Test that deep validation fails for empty CSV files."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/sample.csv",
        )

        # Create directories and files
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()
        (tmp_path / "public/description.md").write_text("Test description")

        # Create empty CSV files
        pd.DataFrame().to_csv(tmp_path / "private/answers.csv", index=False)
        pd.DataFrame().to_csv(tmp_path / "public/sample.csv", index=False)

        assert is_dataset_prepared(competition) is True
        assert is_dataset_prepared(competition, deep=True) is False

    def test_deep_validation_corrupt_csv(self, tmp_path):
        """Test that deep validation fails for corrupt CSV files."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/sample.csv",
        )

        # Create directories and files
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()
        (tmp_path / "public/description.md").write_text("Test description")

        # Create corrupt CSV files
        (tmp_path / "private/answers.csv").write_text("not,a,valid,csv,file {{{")
        (tmp_path / "public/sample.csv").write_text("col1,col2\n1,2\n3,4")

        assert is_dataset_prepared(competition) is True
        assert is_dataset_prepared(competition, deep=True) is False

    def test_deep_validation_all_nan_columns(self, tmp_path):
        """Test that deep validation warns about all-NaN columns but still passes."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/sample.csv",
        )

        # Create directories and files
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()
        (tmp_path / "public/description.md").write_text("Test description")

        # Create CSV with some NaN columns
        df = pd.DataFrame({
            "valid_col": [1, 2, 3],
            "all_nan_col": [None, None, None],
            "another_valid": [4, 5, 6]
        })
        df.to_csv(tmp_path / "private/answers.csv", index=False)
        df.to_csv(tmp_path / "public/sample.csv", index=False)

        # Should still pass, but with a warning logged
        assert is_dataset_prepared(competition, deep=True) is True

    def test_deep_validation_whitespace_column_names(self, tmp_path):
        """Test that deep validation fails for whitespace-only column names."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/sample.csv",
        )

        # Create directories and files
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()
        (tmp_path / "public/description.md").write_text("Test description")

        # Create CSV with whitespace-only column name
        # We need to manually create the CSV since pandas normalizes column names
        with open(tmp_path / "private/answers.csv", 'w') as f:
            f.write("col1,  ,col2\n1,4,7\n2,5,8\n3,6,9")
        with open(tmp_path / "public/sample.csv", 'w') as f:
            f.write("col1,  ,col2\n1,4,7\n2,5,8\n3,6,9")

        assert is_dataset_prepared(competition) is True
        # Deep validation should fail due to whitespace column name
        assert is_dataset_prepared(competition, deep=True) is False

    def test_deep_validation_multiple_csv_files(self, tmp_path):
        """Test that deep validation validates all CSV files in directories."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/sample.csv",
        )

        # Create directories and files
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()
        (tmp_path / "public/description.md").write_text("Test description")

        # Create multiple CSV files
        df1 = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        df2 = pd.DataFrame({"a": [7, 8, 9], "b": [10, 11, 12]})

        df1.to_csv(tmp_path / "private/answers.csv", index=False)
        df1.to_csv(tmp_path / "public/sample.csv", index=False)
        df2.to_csv(tmp_path / "public/train.csv", index=False)
        df2.to_csv(tmp_path / "private/train.csv", index=False)

        assert is_dataset_prepared(competition, deep=True) is True

    def test_deep_validation_backward_compatibility(self, tmp_path):
        """Test that deep=False maintains backward compatibility."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/sample.csv",
        )

        # Create directories and files
        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()

        # Create CSV files without description.md
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        df.to_csv(tmp_path / "private/answers.csv", index=False)
        df.to_csv(tmp_path / "public/sample.csv", index=False)

        # deep=False (default) should pass
        assert is_dataset_prepared(competition, deep=False) is True

    def test_directory_sample_submission_is_accepted_for_artifact_tasks(self, tmp_path):
        """Directory-style artifact tasks should pass prepared checks."""
        competition = MockCompetition(
            public_dir=tmp_path / "public",
            private_dir=tmp_path / "private",
            answers=tmp_path / "private/answers.csv",
            sample_submission=tmp_path / "public/pred_results",
            evaluator_config={
                "submission": {
                    "root_kind": "directory",
                }
            },
        )

        (tmp_path / "public").mkdir()
        (tmp_path / "private").mkdir()
        (tmp_path / "public/description.md").write_text("Test description")
        (tmp_path / "public/pred_results").mkdir()

        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        df.to_csv(tmp_path / "private/answers.csv", index=False)
        df.to_csv(tmp_path / "public/pred_results/sample.csv", index=False)

        assert is_dataset_prepared(competition) is True
        assert is_dataset_prepared(competition, deep=True) is True
