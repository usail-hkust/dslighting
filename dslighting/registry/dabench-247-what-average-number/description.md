# DABench Task 247 - What is the average number of runs scored by players who are eligible for free agency compared to players who are not eligible for free agency?

## Task Description

What is the average number of runs scored by players who are eligible for free agency compared to players who are not eligible for free agency?

## Concepts

Summary Statistics

## Data Description

Dataset file: `baseball_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the 'groupby' function on the 'indicator_of_free_agency_eligibility' column to group the data by whether a player is eligible for free agency or not. Then use the 'mean' function on the 'number_of_runs' column to find the average number of runs scored by these two groups of players.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `247`
- `answer`: two key-value pairs separated by a space: `@average_runs_by_not_eligible_for_free_agency[<average_runs>] @average_runs_by_eligible_for_free_agency[<average_runs>]`

Each `<average_runs>` is a float rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
