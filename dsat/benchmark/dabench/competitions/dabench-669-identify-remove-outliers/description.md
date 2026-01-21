# DABench Task 669 - Identify and remove any outliers in the MedInc column of the provided dataset using the IQR method. Then calculate the mean and standard deviation of the cleaned MedInc column.

## Task Description

Identify and remove any outliers in the MedInc column of the provided dataset using the IQR method. Then calculate the mean and standard deviation of the cleaned MedInc column.

## Concepts

Outlier Detection, Summary Statistics

## Data Description

Dataset file: `my_test_01.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Identify an outlier as any value that falls below Q1 - 1.5 * IQR or above Q3 + 1.5 * IQR, where Q1 and Q3 are the first and third quartiles, respectively, and IQR is the interquartile range (Q3 - Q1). Calculate the mean and standard deviation to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@standard_deviation[standard_deviation_value] @mean[mean_value]

"mean_value" and "standard_deviation_value" are floats rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
