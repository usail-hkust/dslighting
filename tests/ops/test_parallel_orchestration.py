"""Tests for parallel.py majority aggregation strategy."""

from pathlib import Path

import pytest

# Bypass dslighting __init__ by importing the module file directly
import importlib.util

# Load the parallel module directly without triggering dslighting __init__
parallel_path = (
    Path(__file__).resolve().parents[2]
    / "dslighting"
    / "ops"
    / "orchestration"
    / "parallel.py"
)

spec = importlib.util.spec_from_file_location("parallel_module", parallel_path)
parallel_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parallel_module)

Parallel = parallel_module.Parallel


class TestParallelMajorityVoting:
    """Test majority voting aggregation strategy."""

    @pytest.mark.asyncio
    async def test_majority_with_clear_winner(self):
        """Test majority vote with clear >50% winner."""
        # Create mock operators that return async results
        async def op1(**kwargs):
            return "answer_a"

        async def op2(**kwargs):
            return "answer_a"

        async def op3(**kwargs):
            return "answer_b"

        parallel = Parallel([op1, op2, op3], aggregation="majority")
        result = await parallel.execute()

        assert result == "answer_a"

    @pytest.mark.asyncio
    async def test_majority_all_same(self):
        """Test majority vote when all results are identical."""
        async def op1(**kwargs):
            return "same_answer"

        async def op2(**kwargs):
            return "same_answer"

        async def op3(**kwargs):
            return "same_answer"

        parallel = Parallel([op1, op2, op3], aggregation="majority")
        result = await parallel.execute()

        assert result == "same_answer"

    @pytest.mark.asyncio
    async def test_majority_no_clear_winner_50_50(self):
        """Test majority vote with 50-50 tie (no >50% majority)."""
        async def op1(**kwargs):
            return "answer_a"

        async def op2(**kwargs):
            return "answer_a"

        async def op3(**kwargs):
            return "answer_b"

        async def op4(**kwargs):
            return "answer_b"

        parallel = Parallel([op1, op2, op3, op4], aggregation="majority")
        result = await parallel.execute()

        # Should return first result with warning
        assert result == "answer_a"

    @pytest.mark.asyncio
    async def test_majority_no_winner_33_split(self):
        """Test majority vote with 3-way split (no majority)."""
        async def op1(**kwargs):
            return "answer_a"

        async def op2(**kwargs):
            return "answer_b"

        async def op3(**kwargs):
            return "answer_c"

        parallel = Parallel([op1, op2, op3], aggregation="majority")
        result = await parallel.execute()

        # Should return first result with warning
        assert result == "answer_a"

    @pytest.mark.asyncio
    async def test_majority_single_result(self):
        """Test majority vote with single result."""
        async def op1(**kwargs):
            return "only_answer"

        parallel = Parallel([op1], aggregation="majority")
        result = await parallel.execute()

        assert result == "only_answer"

    @pytest.mark.asyncio
    async def test_majority_with_numeric_results(self):
        """Test majority vote with numeric results."""
        async def op1(**kwargs):
            return 42

        async def op2(**kwargs):
            return 42

        async def op3(**kwargs):
            return 100

        parallel = Parallel([op1, op2, op3], aggregation="majority")
        result = await parallel.execute()

        assert result == 42

    @pytest.mark.asyncio
    async def test_majority_with_dict_results(self):
        """Test majority vote with dictionary results."""
        dict_a = {"answer": "a", "confidence": 0.9}
        dict_b = {"answer": "b", "confidence": 0.7}

        async def op1(**kwargs):
            return dict_a

        async def op2(**kwargs):
            return dict_a

        async def op3(**kwargs):
            return dict_b

        parallel = Parallel([op1, op2, op3], aggregation="majority")
        result = await parallel.execute()

        assert result == dict_a

    @pytest.mark.asyncio
    async def test_majority_5_operators_3_winner(self):
        """Test majority with 5 operators where 3 agree."""
        async def op1(**kwargs):
            return "win"

        async def op2(**kwargs):
            return "win"

        async def op3(**kwargs):
            return "win"

        async def op4(**kwargs):
            return "lose"

        async def op5(**kwargs):
            return "lose"

        parallel = Parallel([op1, op2, op3, op4, op5], aggregation="majority")
        result = await parallel.execute()

        assert result == "win"


class TestParallelOtherStrategies:
    """Test other aggregation strategies still work."""

    @pytest.mark.asyncio
    async def test_first_success_returns_first(self):
        """Test first_success returns first successful result."""
        async def op1(**kwargs):
            return "first"

        async def op2(**kwargs):
            return "second"

        async def op3(**kwargs):
            return "third"

        parallel = Parallel([op1, op2, op3], aggregation="first_success")
        result = await parallel.execute()

        assert result == "first"

    @pytest.mark.asyncio
    async def test_all_returns_all_results(self):
        """Test all aggregation returns list of all results."""
        async def op1(**kwargs):
            return "result_1"

        async def op2(**kwargs):
            return "result_2"

        async def op3(**kwargs):
            return "result_3"

        parallel = Parallel([op1, op2, op3], aggregation="all")
        result = await parallel.execute()

        assert isinstance(result, list)
        assert len(result) == 3
        assert "result_1" in result
        assert "result_2" in result
        assert "result_3" in result

    @pytest.mark.asyncio
    async def test_best_with_scores(self):
        """Test best aggregation with scored results."""
        async def op1(**kwargs):
            return {"text": "answer1", "score": 0.8}

        async def op2(**kwargs):
            return {"text": "answer2", "score": 0.95}

        async def op3(**kwargs):
            return {"text": "answer3", "score": 0.7}

        parallel = Parallel([op1, op2, op3], aggregation="best")
        result = await parallel.execute()

        assert result["text"] == "answer2"
        assert result["score"] == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
