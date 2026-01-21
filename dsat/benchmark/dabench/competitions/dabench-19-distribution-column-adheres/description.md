# DABench Task 19 - Check if the distribution of the "Mar.2020" column adheres to a normal distribution.

## Task Description

Check if the distribution of the "Mar.2020" column adheres to a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `unemployement_industry.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Assume a normal distribution if skewness is between -0.5 and 0.5. Use the Fisher-Pearson coefficient of skewness. Round results to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `19`
- `answer`: `@is_normal[<Yes/No>]` depending on whether the skewness lies within the specified boundaries.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
