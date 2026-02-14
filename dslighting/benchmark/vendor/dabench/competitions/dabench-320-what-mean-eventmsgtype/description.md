# DABench Task 320 - What is the mean of the EVENTMSGTYPE column?

## Task Description

What is the mean of the EVENTMSGTYPE column?

## Concepts

Summary Statistics

## Data Description

Dataset file: `0020200722.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

To calculate the arithmetic mean of all the observations in the EVENTMSGTYPE column. Ignore any missing values or outliers when calculating the mean.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `320`
- `answer`: `@mean_eventmsgtype[<mean>]` where `<mean>` is the mean value rounded as needed.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
