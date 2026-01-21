# DABench Task 690 - 2. Perform outlier detection on the wind speed column using Z-scores. Identify the number of outliers and provide the values of the outliers. After removing the outliers, calculate the mean and standard deviation of the wind speed column.

## Task Description

2. Perform outlier detection on the wind speed column using Z-scores. Identify the number of outliers and provide the values of the outliers. After removing the outliers, calculate the mean and standard deviation of the wind speed column.

## Concepts

Outlier Detection, Summary Statistics

## Data Description

Dataset file: `ravenna_250715.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Identify outliers using Z-score method considering points that have Z-score greater than 3 or less than -3 as outliers. After outlier detection, remove these identified outliers from the dataset and calculate the mean and standard deviation of the wind speed column.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@mean_wind_speed[number, rounded to 2 decimal places] @std_deviation_wind_speed[number, rounded to 2 decimal places] @number_of_outliers[integer]

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
