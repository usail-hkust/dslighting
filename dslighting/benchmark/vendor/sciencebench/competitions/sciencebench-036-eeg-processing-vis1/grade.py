"""
Grade EEG processing visualization task using visual similarity.

This grader compares the predicted image with the gold standard image
using image similarity metrics.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image
from typing import Union

from dslighting.benchmark.grading.models import GradingRequest


def calculate_image_similarity(pred_image: np.ndarray, gold_image: np.ndarray) -> float:
    """
    Calculate similarity between two images using multiple metrics.

    Args:
        pred_image: Predicted image as numpy array
        gold_image: Gold standard image as numpy array

    Returns:
        Similarity score between 0 and 100
    """
    # Resize if dimensions don't match
    if pred_image.shape != gold_image.shape:
        from PIL import Image
        pred_pil = Image.fromarray(pred_image)
        pred_pil = pred_pil.resize((gold_image.shape[1], gold_image.shape[0]), Image.LANCZOS)
        pred_image = np.array(pred_pil)

    # Convert to float and normalize
    pred_float = pred_image.astype(np.float32) / 255.0
    gold_float = gold_image.astype(np.float32) / 255.0

    # Calculate Mean Squared Error
    mse = np.mean((pred_float - gold_float) ** 2)

    # Calculate PSNR (Peak Signal-to-Noise Ratio)
    if mse == 0:
        psnr = 100.0
    else:
        psnr = 20 * np.log10(1.0 / np.sqrt(mse))

    # Calculate Structural Similarity (simplified version)
    # Using correlation coefficient as a proxy
    pred_flat = pred_float.flatten()
    gold_flat = gold_float.flatten()

    correlation = np.corrcoef(pred_flat, gold_flat)[0, 1]

    # Combine metrics
    # PSNR typically ranges from 20-40 for similar images
    # Normalize PSNR to 0-100 scale (assuming 20-40 range)
    psnr_normalized = min(100, max(0, (psnr - 20) * 5))

    # Correlation ranges from -1 to 1, normalize to 0-100
    correlation_normalized = (correlation + 1) * 50

    # Weighted average
    similarity_score = 0.6 * psnr_normalized + 0.4 * correlation_normalized

    return float(similarity_score)


def grade(request: GradingRequest) -> float:
    """
    Grade the submission by comparing with gold standard image.

    Args:
        request: GradingRequest containing submission path and references

    Returns:
        Score: 1.0 if similarity >= 60, 0.0 otherwise
    """
    submission_path = request.submission.root
    # For task 36, the answers is a PNG file directly
    answers_path = request.references.private_dir / "biopsykit_eeg_processing_vis1_gold.png"

    # Check if files exist
    if not submission_path.exists():
        raise FileNotFoundError(f"Submission file not found: {submission_path}")

    if not answers_path.exists():
        raise FileNotFoundError(f"Gold standard file not found: {answers_path}")

    # Load images
    try:
        pred_image = Image.open(submission_path)
        pred_array = np.array(pred_image.convert('RGB'))
    except Exception as e:
        raise ValueError(f"Failed to load prediction image: {e}")

    try:
        gold_image = Image.open(answers_path)
        gold_array = np.array(gold_image.convert('RGB'))
    except Exception as e:
        raise ValueError(f"Failed to load gold standard image: {e}")

    # Calculate similarity
    similarity_score = calculate_image_similarity(pred_array, gold_array)

    # Threshold at 60
    threshold = 60.0

    # Return binary score (1.0 if pass, 0.0 if fail)
    if similarity_score >= threshold:
        return 1.0
    else:
        return 0.0


if __name__ == "__main__":
    # Test grading
    import sys
    if len(sys.argv) > 2:
        pred_path = sys.argv[1]
        gold_path = sys.argv[2]
        score = grade(pred_path, gold_path)
        print(f"Similarity score: {score}")
