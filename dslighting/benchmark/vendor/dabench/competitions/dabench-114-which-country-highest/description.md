# DABench Task 114 - Which country has the highest happiness score?

## Task Description

Which country has the highest happiness score?

## Concepts

Summary Statistics

## Data Description

Dataset file: `2015.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Find the country with the highest happiness score in the dataset. If two or more countries have the same highest happiness score, return all of them.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `114`
- `answer`: `@country_with_highest_score[<country_name>]`

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
