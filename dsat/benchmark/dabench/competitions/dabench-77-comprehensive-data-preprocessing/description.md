# DABench Task 77 - Perform comprehensive data preprocessing on the "Date" column to extract the month and year information. Calculate the average closing price for each month and year combination. Return the month and year combination which has the highest average closing price.

## Task Description

Perform comprehensive data preprocessing on the "Date" column to extract the month and year information. Calculate the average closing price for each month and year combination. Return the month and year combination which has the highest average closing price.

## Concepts

Comprehensive Data Preprocessing, Summary Statistics

## Data Description

Dataset file: `microsoft.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Set the start of each month to be the first day of the month and the end of the month to be the last day of the month.
The calculation of the average closing price should be done using the arithmetic mean. 
For ties, return the most recent month and year combination.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `77`
- `answer`: `@Highest_Monthly_Average_Close_Price[<month, year, average_close_price>]` where `month` is 1–12, `year` is an integer, and `average_close_price` is a float rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
