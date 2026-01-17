# DABench Task 415 - What is the distribution of fare paid by male passengers who survived? Are there any significant differences in the fare paid by male passengers who survived compared to male passengers who did not survive?

## Task Description

What is the distribution of fare paid by male passengers who survived? Are there any significant differences in the fare paid by male passengers who survived compared to male passengers who did not survive?

## Concepts

Distribution Analysis, Comprehensive Data Preprocessing

## Data Description

Dataset file: `titanic_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean and standard deviation of fares paid by male passengers who survived and did not survive separately.
Conduct an independent sample t-test to compare the means of these two groups.
Use a significance level of 0.05.
Report whether there is a significant difference in the means based on the p-value of the test.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@survived_fare_mean[mean_survived] @not_survived_fare_std[std_not_survived] @fare_difference_significance[significance] @not_survived_fare_mean[mean_not_survived] @survived_fare_std[std_survived]

"mean_survived" and "std_survived" are the mean and std of fares for male passengers who survived (rounded to two decimals). "mean_not_survived" and "std_not_survived" are the mean and std for those who did not survive (rounded to two decimals). "significance" is "significant" or "not significant" based on the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
