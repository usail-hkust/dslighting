# DABench Task 757 - 3. Are there any outliers in the observation values (obs_value) column? If yes, how many outliers are there using the interquartile range method?

## Task Description

3. Are there any outliers in the observation values (obs_value) column? If yes, how many outliers are there using the interquartile range method?

## Concepts

Outlier Detection

## Data Description

Dataset file: `weather_data_1864.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the interquartile range (IQR) for obs_value. Any value that falls below Q1 - 1.5*IQR or above Q3 + 1.5*IQR is considered an outlier. Count the number of outliers according to this method.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@outlier_count[total_outlier]

"total_outlier" is an integer representing the number of outliers. If there are no outliers, output @outlier_status["No Outliers Detected"] instead.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
