# DABench Task 243 - What is the mean batting average of the players in the dataset?

## Task Description

What is the mean batting average of the players in the dataset?

## Concepts

Summary Statistics

## Data Description

Dataset file: `baseball_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Consider only the players who have a recorded batting average. Do not include the one player with a missing batting average into your calculation. Report your answer rounded off to three decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `243`
- `answer`: `@mean_batting_average[<mean_batting_average>]` where the value is between 0 and 1, rounded to three decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
