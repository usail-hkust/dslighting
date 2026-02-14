# DABench Task 724 - 3. Perform outlier detection on the 'acceleration' column using the Z-score method. Identify any outliers and remove them from the dataset. Recalculate the mean and standard deviation of the 'acceleration' column after removing the outliers.

## Task Description

3. Perform outlier detection on the 'acceleration' column using the Z-score method. Identify any outliers and remove them from the dataset. Recalculate the mean and standard deviation of the 'acceleration' column after removing the outliers.

## Concepts

Outlier Detection, Summary Statistics, Comprehensive Data Preprocessing

## Data Description

Dataset file: `auto-mpg.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Consider observations as outliers if their Z-scores are outside of the -3 to 3 range. For the "average acceleration" after outlier removal, calculate it using the arithmetic mean formula. Calculate the standard deviation using the population standard deviation formula, not the sample standard deviation formula. Round both measures to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@std_acceleration[acceleration_std] @mean_acceleration[avg_acceleration]

"acceleration_std" and "avg_acceleration" are numbers rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
