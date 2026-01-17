# DABench Task 123 - Which country has the highest average number of daily vaccinations per million people?

## Task Description

Which country has the highest average number of daily vaccinations per million people?

## Concepts

Summary Statistics, Distribution Analysis

## Data Description

Dataset file: `country_vaccinations.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Based on the current available data without null values in the column of daily vaccinations per million people.
No tie of the maximum value is allowed. In case of a tie, consider the country with the first appeared maximum value.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `123`
- `answer`: `@country_with_highest_average_daily_vaccinations[<country_name>]` where `<country_name>` is the string answer.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
