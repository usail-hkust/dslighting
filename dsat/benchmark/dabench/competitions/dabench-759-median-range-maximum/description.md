# DABench Task 759 - 5. Calculate the median and range of the maximum temperature (TMAX_F) for each type of observation (obs_type) recorded in the dataset. Are there any differences in the median and range between different observation types?

## Task Description

5. Calculate the median and range of the maximum temperature (TMAX_F) for each type of observation (obs_type) recorded in the dataset. Are there any differences in the median and range between different observation types?

## Concepts

Summary Statistics, Distribution Analysis

## Data Description

Dataset file: `weather_data_1864.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

In your analysis:
- Consider only two observation types: "TMAX" and "TMIN".
- Report the median rounded to two decimal places.
- Calculate the range as the difference between the maximum and minimum temperatures for each observation type.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@range_tmax["range_TMAX"] @median_tmax["median_TMAX"]

"range_TMAX" is the range of temperatures for the TMAX observation type (greater than 0). "median_TMAX" is the median temperature for the TMAX observation type, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
