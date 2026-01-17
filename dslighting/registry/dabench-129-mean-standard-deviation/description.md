# DABench Task 129 - Calculate the mean and standard deviation of the fare paid by the passengers.

## Task Description

Calculate the mean and standard deviation of the fare paid by the passengers.

## Concepts

Summary Statistics

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the arithmetic mean and population standard deviation (σ). For the mean, sum up all fare and divide by the count of the data points. For the standard deviation, use the formula:
σ = sqrt(sum for i = 1 to n (xi - μ)^2/n), where xi is each fare and μ is the mean fare, n is the count of the fare data points.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `129`
- `answer`: `@std_dev_fare[<std_dev_value>]` where the value is rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
