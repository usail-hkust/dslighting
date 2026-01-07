# DABench Task 542 - What is the mean length of the abalone in mm?

## Task Description

What is the mean length of the abalone in mm?

## Concepts

Summary Statistics

## Data Description

Dataset file: `abalone.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Perform arithmetical mean operation on the length column, use rounded number to two decimal places as the answer.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `542`
- `answer`: `@mean_length[<mean_length_value>]`, a number between 1 and 999 rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
