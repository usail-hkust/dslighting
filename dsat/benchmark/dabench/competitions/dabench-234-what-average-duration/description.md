# DABench Task 234 - What is the average duration of a budget year for all departments?

## Task Description

What is the average duration of a budget year for all departments?

## Concepts

Summary Statistics

## Data Description

Dataset file: `city_departments_in_current_budget.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the duration of each department’s budget year in days, by subtracting the budget_year_start from budget_year_end. Afterwards, calculate the mean of these durations using a built-in Python function.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `234`
- `answer`: `@average_duration[<days>]` where `<days>` is the average number of days (whole number).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
