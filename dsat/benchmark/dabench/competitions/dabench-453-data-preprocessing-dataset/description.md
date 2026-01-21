# DABench Task 453 - 2. Perform data preprocessing on the dataset, which includes removing outliers in the wind speed (WINDSPEED) column using the Z-score method (outliers are values that have a Z-score greater than 3 or lesser than -3) and handling missing values in the atmospheric temperature (AT) column by replacing them with the mean temperature. After preprocessing, calculate the mean wind speed and average atmospheric temperature.

## Task Description

2. Perform data preprocessing on the dataset, which includes removing outliers in the wind speed (WINDSPEED) column using the Z-score method (outliers are values that have a Z-score greater than 3 or lesser than -3) and handling missing values in the atmospheric temperature (AT) column by replacing them with the mean temperature. After preprocessing, calculate the mean wind speed and average atmospheric temperature.

## Concepts

Comprehensive Data Preprocessing, Summary Statistics

## Data Description

Dataset file: `baro_2015.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean and standard deviation of the wind speed (WINDSPEED) column before preprocessing.
Replace any wind speed value that is more than three standard deviations away from the mean, with the mean wind speed.
Calculate the mean atmosphere temperature (AT), and fill missing values in the atmospheric temperature (AT) column with this mean.
Calculate the mean values after preprocessing.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@mean_wind_pre[mean_wind_pre] @mean_atmos_temp_pre[mean_atmos_temp_pre] @mean_atmos_temp_post[mean_atmos_temp_post] @mean_wind_post[mean_wind_post]

"mean_wind_pre" and "mean_wind_post" are the mean wind speed values before and after preprocessing, rounded to two decimal places. "mean_atmos_temp_pre" and "mean_atmos_temp_post" are the mean atmospheric temperature values before and after preprocessing, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
