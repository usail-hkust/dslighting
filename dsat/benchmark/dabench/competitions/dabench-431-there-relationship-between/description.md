# DABench Task 431 - 1. Is there a relationship between the maximum storm category achieved by a storm and the duration of its activity? How does this relationship differ between storms causing high and low damage?

## Task Description

1. Is there a relationship between the maximum storm category achieved by a storm and the duration of its activity? How does this relationship differ between storms causing high and low damage?

## Concepts

Correlation Analysis, Comprehensive Data Preprocessing

## Data Description

Dataset file: `cost_data_with_errors.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between maximum storm category and the duration of activity for storms that caused damage above and below the median damage level.
Assess the significance of the correlation using a two-tailed test with a significance level (alpha) of 0.05.
Report the p-value associated with the correlation test.
Consider the relationship to be linear if the p-value is less than 0.05 and the absolute value of r is greater than or equal to 0.4.
Consider the relationship to be nonlinear if the p-value is less than 0.05 and the absolute value of r is less than 0.4.
If the p-value is greater than or equal to 0.05, report that there is no significant correlation.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@high_damage_relationship_type[relationship_type] @high_damage_correlation_coefficient[r_value] @high_damage_p_value[p_value]

"r_value" is a number between -1 and 1 (two decimals). "p_value" is between 0 and 1 (four decimals). "relationship_type" is "linear", "nonlinear", or "none".

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
