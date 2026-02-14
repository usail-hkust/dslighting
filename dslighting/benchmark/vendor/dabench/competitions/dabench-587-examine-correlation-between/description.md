# DABench Task 587 - Examine the correlation between the average number of agents talking and the average waiting time for callers.

## Task Description

Examine the correlation between the average number of agents talking and the average waiting time for callers.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `20170413_000000_group_statistics.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Transform the average waiting time from 'HH:MM:SS' string format to seconds (integer type). Then use the Pearson's method to calculate the correlation coefficient between the average number of agents talking and the transformed average waiting time. The result should be rounded to three decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `587`
- `answer`: `@correlation_coefficient[<float>]`, a number between -1 and 1 rounded to three decimals describing the correlation between average agents talking and average waiting time.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
