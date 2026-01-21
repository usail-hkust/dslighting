# DABench Task 450 - 2. Calculate the average wind speed (WINDSPEED) for each month in the dataset.

## Task Description

2. Calculate the average wind speed (WINDSPEED) for each month in the dataset.

## Concepts

Summary Statistics

## Data Description

Dataset file: `baro_2015.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Assume that the "DATE TIME" column is in the format "YYYY-MM-DD HH:MM:SS". Extract the month from each date and calculate the mean wind speed for each respective month. Keep only two decimal places. The data is in chronological order so the answer should also be in order.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@monthly_avg_windspeed[{'month_1':avg_1, 'month_2':avg_2, ..., 'month_12':avg_12}]

Keep months in chronological order; values rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
