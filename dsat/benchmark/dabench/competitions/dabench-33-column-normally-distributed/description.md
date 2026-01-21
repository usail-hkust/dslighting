# DABench Task 33 - Is the "row m/z" column normally distributed?

## Task Description

Is the "row m/z" column normally distributed?

## Concepts

Distribution Analysis

## Data Description

Dataset file: `imp.score.ldlr.metabolome.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Kolmogorov-Smirnov test to assess the normality of the "row m/z" column. Consider the distribution to be normal if the Kolmogorov-Smirnov test's p-value is greater than or equal to 0.05. Use a significance level (alpha) of 0.05. If the p-value is greater than or equal to 0.05, report that the data is normally distributed. If not, report that the data is not normally distributed. Ignore any null or missing values in performing the test.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `33`
- `answer`: `@normality_decision[<decision>]` where `<decision>` is either `normally distributed` or `not normally distributed`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
