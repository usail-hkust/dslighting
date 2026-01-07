# DABench Task 429 - 2. Is there a correlation between the maximum storm category achieved by a storm and the recorded damage in USD? If so, what is the strength and direction of the correlation?

## Task Description

2. Is there a correlation between the maximum storm category achieved by a storm and the recorded damage in USD? If so, what is the strength and direction of the correlation?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `cost_data_with_errors.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between maximum storm category and damage in USD.
Use a two-tailed test with a significance level (alpha) of 0.05 to assess the significance of the correlation. 
Report the p-value associated with the correlation test.
If the p-value is less than 0.05 and the absolute value of r is greater than or equal to 0.5, infer the relationship to be linear.
If the p-value is less than 0.05 and the absolute value of r is less than 0.5, infer the relationship to be nonlinear.
If the p-value is greater than or equal to 0.05, report that there is no significant correlation.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@correlation_coefficient[r_value] @relationship_type[relationship_type] @p_value[p_value]

"r_value" is a number between -1 and 1, rounded to 2 decimal places. "p_value" is between 0 and 1, rounded to 4 decimal places. "relationship_type" is "linear", "nonlinear", or "none" based on the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
