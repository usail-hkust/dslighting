# DABench Task 139 - Question 2: Are the percentage of votes received by the Democratic party in a particular county normally distributed?

## Task Description

Question 2: Are the percentage of votes received by the Democratic party in a particular county normally distributed?

## Concepts

Distribution Analysis

## Data Description

Dataset file: `election2016.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{Test whether the 'per_dem' column follows a normal distribution using the Shapiro-Wilk test for normality. Set the significance level (alpha) at 0.05. If p-value is less than 0.05, reject the null hypothesis and report that the data is not normally distributed. If p-value is greater than or equal to 0.05, fail to reject the null hypothesis and report that the data is normally distributed.}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `139`
- `answer`: `@normality_status[<status>]` where `<status>` is `normal` or `not normal`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
