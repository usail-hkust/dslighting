# DABench Task 668 - Calculate the correlation coefficient between the HouseAge and MedianHouseValue columns in the provided dataset.

## Task Description

Calculate the correlation coefficient between the HouseAge and MedianHouseValue columns in the provided dataset.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `my_test_01.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient to assess the strength and direction of the linear relationship between HouseAge and MedianHouseValue. Report the p-value associated with the correlation test with a significance level of 0.05. Indicate whether or not there is a significant correlation based on the p-value.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@correlation_coefficient[r_value] @p_value[p_value] @significant_correlation[significant_correlation]

"r_value" is between -1 and 1, rounded to two decimals; "p_value" is between 0 and 1, rounded to four decimals; "significant_correlation" is a boolean indicating significance (true/false).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
