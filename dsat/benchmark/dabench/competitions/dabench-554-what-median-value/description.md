# DABench Task 554 - What is the median HT_M value for the plant species with a CON value of 1, and a PLTID of 5?

## Task Description

What is the median HT_M value for the plant species with a CON value of 1, and a PLTID of 5?

## Concepts

Summary Statistics, Distribution Analysis

## Data Description

Dataset file: `tree.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Filter the data frame first by CON value of 1, then by PLTID of 5, calculate the median HT_M value of these entries.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `554`
- `answer`: `@median_ht_m[<median_value>]` where `<median_value>` is a float rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
