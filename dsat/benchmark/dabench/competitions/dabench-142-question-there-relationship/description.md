# DABench Task 142 - Question 2: Is there a relationship between the difference in votes received by the Democratic and Republican parties and their percentage point difference?

## Task Description

Question 2: Is there a relationship between the difference in votes received by the Democratic and Republican parties and their percentage point difference?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `election2016.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between the difference in votes and the percentage point difference. Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05. Report the p-value associated with the correlation test. Consider the relationship to be linear if the p-value is less than 0.05 and the absolute value of r is greater than or equal to 0.5. Consider the relationship to be nonlinear if the p-value is less than 0.05 and the absolute value of r is less than 0.5. If the p-value is greater than or equal to 0.05, report that there is no significant correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `142`
- `answer`: three key-value pairs separated by spaces: `@relationship_type[<relationship_type>] @correlation_coefficient[<r_value>] @p_value[<p_value>]`

`<r_value>` is between -1 and 1 (two decimals); `<p_value>` is between 0 and 1 (four decimals); `<relationship_type>` is `linear`, `nonlinear`, or `none`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
