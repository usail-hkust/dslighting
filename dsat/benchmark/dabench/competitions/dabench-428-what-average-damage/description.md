# DABench Task 428 - 1. What is the average damage in USD caused by storms in each year from 2000 to 2010? Are there any significant differences in the average damage between years?

## Task Description

1. What is the average damage in USD caused by storms in each year from 2000 to 2010? Are there any significant differences in the average damage between years?

## Concepts

Summary Statistics, Distribution Analysis

## Data Description

Dataset file: `cost_data_with_errors.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Calculate the mean damage in USD for each year.
Perform a one-way Analysis of Variance (ANOVA) to test whether there are significant differences in the average damage between years.
The significance level (alpha) for the ANOVA test should be 0.05.
Report the p-value associated with the ANOVA test.
If the p-value is less than 0.05, infer that there are significant differences.
If the p-value is greater than or equal to 0.05, infer that there are no significant differences.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@p_value[p_value] @difference_type[difference_type]

"p_value" is a number between 0 and 1, rounded to 4 decimal places. "difference_type" is "significant" or "none" based on the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
