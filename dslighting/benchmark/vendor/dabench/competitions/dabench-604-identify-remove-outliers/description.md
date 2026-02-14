# DABench Task 604 - 1. Identify and remove any outliers in the SWX column using the Z-score method with a threshold of 3. Calculate the new mean and standard deviation of the SWX column after removing the outliers.

## Task Description

1. Identify and remove any outliers in the SWX column using the Z-score method with a threshold of 3. Calculate the new mean and standard deviation of the SWX column after removing the outliers.

## Concepts

Outlier Detection, Summary Statistics

## Data Description

Dataset file: `well_2_complete.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Use z-score for outlier detection with a threshold of 3, i.e, any data point that has a z-score greater than 3 or less than -3 is considered an outlier.
The mean and standard deviation should be calculated up to 3 decimal places.
Exclude all rows with null values in the SWX column before calculating mean and standard deviation.}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@std_dev_after_removal[std_dev] @outlier_count[outlier_count] @mean_after_removal[mean]

"outlier_count" is an integer. "mean" and "std_dev" are numeric values (up to three decimals).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
