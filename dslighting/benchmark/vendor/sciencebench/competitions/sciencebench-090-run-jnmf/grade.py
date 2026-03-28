"""Grader for ScienceBench task 90 (joint NMF reconstruction)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from dslighting.benchmark.grading.models import GradingRequest

PROPERTY = "conscientiousness"
W_HIGH = f"fit_result_{PROPERTY}_W_high.npy"
W_LOW = f"fit_result_{PROPERTY}_W_low.npy"
H_HIGH = f"fit_result_{PROPERTY}_H_high.npy"
H_LOW = f"fit_result_{PROPERTY}_H_low.npy"
X1_NAME = f"X1_{PROPERTY}.npy"
X2_NAME = f"X2_{PROPERTY}.npy"
X1_THRESHOLD = 34.0
X2_THRESHOLD = 32.0


def _reconstruction_error(x: np.ndarray, w: np.ndarray, h: np.ndarray) -> float:
    reconstruction = w @ h.T
    if reconstruction.shape != x.shape:
        raise ValueError(
            f"Shape mismatch for reconstruction: {reconstruction.shape} vs {x.shape}"
        )
    diff = x - reconstruction
    frob_sq = np.linalg.norm(diff, ord="fro") ** 2
    return frob_sq / x.shape[1]


def _check_non_negative(arr: np.ndarray, name: str) -> bool:
    if np.any(arr < -1e-5):
        print(f"{name} contains negative entries.")
        return False
    return True


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    public_dir = request.references.public_dir

    x1 = np.load(public_dir / "jnmf_data" / X1_NAME)
    x2 = np.load(public_dir / "jnmf_data" / X2_NAME)

    if submission_path.is_file():
        raise ValueError("Submission should be a directory for this task.")

    w_high = np.load(submission_path / W_HIGH)
    w_low = np.load(submission_path / W_LOW)
    h_high = np.load(submission_path / H_HIGH)
    h_low = np.load(submission_path / H_LOW)

    if not all(
        [
            _check_non_negative(w_high, "W_high"),
            _check_non_negative(w_low, "W_low"),
            _check_non_negative(h_high, "H_high"),
            _check_non_negative(h_low, "H_low"),
        ]
    ):
        return 0.0

    x1_err = _reconstruction_error(x1, w_high, h_high)
    x2_err = _reconstruction_error(x2, w_low, h_low)

    print(f"Reconstruction errors — X1: {x1_err}, X2: {x2_err}")

    if x1_err < X1_THRESHOLD and x2_err < X2_THRESHOLD:
        return 1.0
    return 0.0
