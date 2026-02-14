# DABench Task 619 - 1. Identify and remove any outliers in the duration of the trajectories based on the Z-score method where an outlier is defined as a data point that is located outside the whiskers of the box plot (a data point is considered to be an outlier if its z-score is less than -2.5 or greater than 2.5). Calculate the new mean and standard deviation of the trajectory durations after removing the outliers.

## Task Description

1. Identify and remove any outliers in the duration of the trajectories based on the Z-score method where an outlier is defined as a data point that is located outside the whiskers of the box plot (a data point is considered to be an outlier if its z-score is less than -2.5 or greater than 2.5). Calculate the new mean and standard deviation of the trajectory durations after removing the outliers.

## Concepts

Outlier Detection, Summary Statistics

## Data Description

Dataset file: `traj-Osak.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

For outlier detection, use the Z-score method where an outlier is defined as a data point that is located outside the whiskers of the box plot (a data point is considered to be an outlier if its z-score is less than -2.5 or greater than 2.5). For calculating the mean and standard deviation, use the built-in Python functions from numpy. The values should be rounded off to 2 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@std_dev_new[std_dev_value] @mean_new[mean_value]

"mean_value" and "std_dev_value" are numbers rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
