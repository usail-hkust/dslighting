# DABench Task 723 - 2. Generate a new feature called 'power-to-weight ratio' by dividing the horsepower by the weight for each vehicle. Calculate the mean and standard deviation of this new feature.

## Task Description

2. Generate a new feature called 'power-to-weight ratio' by dividing the horsepower by the weight for each vehicle. Calculate the mean and standard deviation of this new feature.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `auto-mpg.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the 'power-to-weight ratio' by dividing the horsepower by the weight for each vehicle, not the other way around. For the "average power-to-weight ratio", calculate it using the arithmetic mean formula. Calculate the standard deviation using the population standard deviation formula, not the sample standard deviation formula. Round both measures to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@mean_ratio[avg_power_weight_ratio] @std_ratio[power_weight_ratio_std]

"avg_power_weight_ratio" and "power_weight_ratio_std" are numbers rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
