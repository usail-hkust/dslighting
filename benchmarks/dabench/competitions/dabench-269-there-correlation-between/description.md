# DABench Task 269 - Is there any correlation between the TOTUSJH and TOTUSJZ columns in the dataset?

## Task Description

Is there any correlation between the TOTUSJH and TOTUSJZ columns in the dataset?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `3901.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient between the TOTUSJH and TOTUSJZ columns. Use a two-tailed test with a significance level of 0.05 to determine the statistical significance. If the p-value is less than 0.05, report the relationship as either "Positive Correlation", "Negative Correlation" or "No Correlation", based on the sign and magnitude of the correlation coefficient. If the p-value is greater than or equal to 0.05, report "No Significant Correlation".

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `269`
- `answer`: three key-value pairs separated by spaces: `@correlation_type[<correlation_type>] @correlation_coefficient[<coefficient>] @p_value[<p_value>]`

`<correlation_type>` is `Positive Correlation`, `Negative Correlation`, `No Correlation`, or `No Significant Correlation`; `<coefficient>` is Pearson r (two decimals); `<p_value>` is rounded to three decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
