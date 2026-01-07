# DABench Task 309 - Perform distribution analysis on the age and fare variables separately, then calculate and compare the skewness and kurtosis values for each. Additionally, count the number of values within one standard deviation from the mean, for both age and fare.

## Task Description

Perform distribution analysis on the age and fare variables separately, then calculate and compare the skewness and kurtosis values for each. Additionally, count the number of values within one standard deviation from the mean, for both age and fare.

## Concepts

Distribution Analysis, Summary Statistics

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use Python's scipy library for your analyses. Calculate skewness and kurtosis values using the scipy.stats.skew() and scipy.stats.kurtosis() functions, respectively, with the default settings. Count the number of values within one standard deviation from the mean by applying standard formula: mean - stdev <= x <= mean + stdev.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `309`
- `answer`: six key-value pairs separated by spaces: `@fare_kurtosis[<kurtosis_value>] @age_values_within_one_stdev[<number>] @fare_skewness[<skewness_value>] @fare_values_within_one_stdev[<number>] @age_skewness[<skewness_value>] @age_kurtosis[<kurtosis_value>]`

`<skewness_value>`/`<kurtosis_value>` are floats with two decimals; `<number>` is a positive integer.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
