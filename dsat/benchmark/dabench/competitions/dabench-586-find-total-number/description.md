# DABench Task 586 - Find out the total number of calls that were abandoned by the callers before being answered by an agent.

## Task Description

Find out the total number of calls that were abandoned by the callers before being answered by an agent.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `20170413_000000_group_statistics.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use Python's pandas DataFrame to load the CSV file. Perform the data cleaning step to ensure there're no null or NaN values for the "num. calls abandoned" column. Then use the sum() function on this column to get the total.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `586`
- `answer`: `@total_abandoned_calls[<integer>]`, the total number of calls abandoned before being answered.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
