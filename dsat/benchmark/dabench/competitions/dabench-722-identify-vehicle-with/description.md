# DABench Task 722 - 1. Identify the vehicle with the highest horsepower and provide its corresponding model year. Calculate the average horsepower along with the standard deviation for all vehicles within the same model year as this vehicle.

## Task Description

1. Identify the vehicle with the highest horsepower and provide its corresponding model year. Calculate the average horsepower along with the standard deviation for all vehicles within the same model year as this vehicle.

## Concepts

Summary Statistics, Comprehensive Data Preprocessing

## Data Description

Dataset file: `auto-mpg.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

For the "average horsepower", calculate it using the arithmetic mean formula. Calculate the standard deviation using the population standard deviation formula, not the sample standard deviation formula. Round both measures to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@highest_horsepower_vehicle[vehicle_model_year] @average_horsepower[same_year_avg_horsepower] @standard_deviation[same_year_horsepower_std]

"vehicle_model_year" is an integer from 1900 to the current year. "same_year_avg_horsepower" and "same_year_horsepower_std" are numbers rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
