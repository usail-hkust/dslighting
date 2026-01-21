# DABench Task 375 - 2. Perform a distribution analysis on the "Trips over the past 24-hours (midnight to 11:59pm)" column. Determine if the distribution adheres to a normal distribution or it exhibits skewness, heavy tails, or bimodality.

## Task Description

2. Perform a distribution analysis on the "Trips over the past 24-hours (midnight to 11:59pm)" column. Determine if the distribution adheres to a normal distribution or it exhibits skewness, heavy tails, or bimodality.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `2014_q4.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use Python's scipy library to perform a Shapiro-Wilk test to check for normality. The Shapiro-Wilk test tests the null hypothesis that the data was drawn from a normal distribution. For skewness and kurtosis use Python's scipy library. Results for skewness and kurtosis are defined as 'heavy' if they fall outside the range of -0.5 to 0.5.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `375`
- `answer`: four key-value pairs separated by spaces: `@skewness[<skewness_value>] @kurtosis[<kurtosis_value>] @shapiro_w[<test_statistic>] @p_value[<p_value>]`

Each value is a float to four decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
