"""Grader for ScienceBench task 95 (synthetic feasibility modeling)."""

from __future__ import annotations

import numpy as np

from benchmarks.sciencebench.grade_helpers import InvalidSubmissionError


def grade(submission, answers) -> float:
    """
    Return the actual evaluation metric (MSE; lower is better).

    `submission` and `answers` are expected to be numpy arrays (loaded by the benchmark).
    """
    pred = submission
    gold = answers

    if pred.shape != gold.shape:
        print(f"Shape mismatch: {pred.shape} vs {gold.shape}")
        raise InvalidSubmissionError(f"Shape mismatch: {pred.shape} vs {gold.shape}")

    mse = float(np.mean((pred - gold) ** 2))
    print(f"MSE: {mse}")
    return mse
