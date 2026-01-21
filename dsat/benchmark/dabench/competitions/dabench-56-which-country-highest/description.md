# DABench Task 56 - Which country has the highest number of deaths recorded in a single year?

## Task Description

Which country has the highest number of deaths recorded in a single year?

## Concepts

Distribution Analysis, Summary Statistics

## Data Description

Dataset file: `estimated_numbers.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the maximum value in the 'No. of deaths' column. Convert the data type of 'No. of deaths' column from Object (string) to Int64 before performing calculations. Ignore those records where 'No. of deaths' column value is Null or empty. Identify the corresponding country and year for the highest number of deaths.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `56`
- `answer`: `@max_deaths_country[<country_name>] @max_deaths_year[<year>]` where `<country_name>` is the country and `<year>` is the integer year of max deaths.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
