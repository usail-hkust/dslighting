# DABench Task 589 - Can we generate a new feature representing the call abandonment rate? If so, what is the call abandonment rate for the timestamp "20170413_080000"?

## Task Description

Can we generate a new feature representing the call abandonment rate? If so, what is the call abandonment rate for the timestamp "20170413_080000"?

## Concepts

Feature Engineering

## Data Description

Dataset file: `20170413_000000_group_statistics.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the call abandonment rate for a specific timestamp as the total number of calls abandoned divided by the total number of calls made during that time. Express the result as a percentage.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `589`
- `answer`: `@abandonment_rate[<abandonment_rate_%>]` where `<abandonment_rate_%>` is a positive real value between 0 and 100 rounded to two decimals, representing the abandonment rate at the specified timestamp.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
