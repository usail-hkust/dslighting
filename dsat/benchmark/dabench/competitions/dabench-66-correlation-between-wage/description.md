# DABench Task 66 - Calculate the correlation between the wage column and the exper column.

## Task Description

Calculate the correlation between the wage column and the exper column.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `beauty and the labor market.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between wage and the exper. Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05. Report the p-value associated with the correlation test. Consider the relationship to be linear if the p-value is less than 0.05 and the absolute value of r is greater than or equal to 0.5. Consider the relationship to be nonlinear if the p-value is less than 0.05 and the absolute value of r is less than 0.5. If the p-value is greater than or equal to 0.05, report that there is no significant correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `66`
- `answer`: two key-value pairs separated by a space: `@correlation_coefficient[<r_value>] @relationship_type[<relationship_type>]`

`<r_value>` is between -1 and 1 (two decimals); `<relationship_type>` is `linear`, `nonlinear`, or `none`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
