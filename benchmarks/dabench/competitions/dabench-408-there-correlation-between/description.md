# DABench Task 408 - Is there a correlation between the fare paid by the passenger and their age? If so, is it a linear or nonlinear correlation?

## Task Description

Is there a correlation between the fare paid by the passenger and their age? If so, is it a linear or nonlinear correlation?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `titanic_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between 'Fare' and 'Age'.
Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05.
Report the p-value associated with the correlation test.
Consider the relationship to be linear if the p-value is less than 0.05 and the absolute value of r is greater than or equal to 0.5.
Consider the relationship to be nonlinear if the p-value is less than 0.05 and the absolute value of r is less than 0.5.
If the p-value is greater than or equal to 0.05, report that there is no significant correlation.
Ignore the null values in 'Age' while calculating the correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@correlation_coefficient[r_value] @relationship_type[relationship_type] @p_value[p_value]

"r_value" is between -1 and 1, rounded to two decimal places. "p_value" is between 0 and 1, rounded to four decimal places. "relationship_type" is "linear", "nonlinear", or "none" based on the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
