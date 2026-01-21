# DABench Task 300 - 1. Is there a correlation between the "nsnps" and "nsamplecov" columns? Calculate the Pearson correlation coefficient (r) to assess the strength of the correlation. Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05. Report the p-value associated with the correlation test. If the p-value is greater than or equal to 0.05, report that there is no significant correlation.

## Task Description

1. Is there a correlation between the "nsnps" and "nsamplecov" columns? Calculate the Pearson correlation coefficient (r) to assess the strength of the correlation. Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05. Report the p-value associated with the correlation test. If the p-value is greater than or equal to 0.05, report that there is no significant correlation.

## Concepts

Correlation Analysis, Comprehensive Data Preprocessing

## Data Description

Dataset file: `ts-sc4-wi100000-sl25000-Qrob_Chr05.tree_table.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between "nsnps" and "nsamplecov". Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05. Report the p-value associated with the correlation test. Consider the relationship to be correlated if the p-value is less than 0.05. If the p-value is greater than or equal to 0.05, report that there is no significant correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `300`
- `answer`: two key-value pairs separated by a space: `@correlation_coefficient[<r_value>] @correlation[<correlation>]`

`<r_value>` is between -1 and 1 (two decimals). `<correlation>` is a string such as `correlated` or `not correlated` describing the relationship.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
