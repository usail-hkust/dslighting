# DABench Task 733 - Apply feature engineering techniques to create a new feature in the dataset that represents the GDP per capita in logarithmic scale (base 10). Implement this feature transformation using Python code.

## Task Description

Apply feature engineering techniques to create a new feature in the dataset that represents the GDP per capita in logarithmic scale (base 10). Implement this feature transformation using Python code.

## Concepts

Feature Engineering

## Data Description

Dataset file: `gapminder_cleaned.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the logarithm with base 10.
While calculating the logarithm, assume all GDP per capita figures are positive.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@has_nan_values_in_new_feature[boolean] @new_feature_mean[mean] @new_feature_std[std]

"boolean" is True or False, indicating whether there are NaN values in the newly created feature. "mean" and "std" are numbers rounded to 2 decimal places representing the mean and standard deviation of the newly created feature.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
