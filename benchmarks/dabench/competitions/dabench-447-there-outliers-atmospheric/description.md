# DABench Task 447 - 2. Are there any outliers in the atmospheric pressure column (BARO)? If yes, how many outliers are there?

## Task Description

2. Are there any outliers in the atmospheric pressure column (BARO)? If yes, how many outliers are there?

## Concepts

Outlier Detection

## Data Description

Dataset file: `baro_2015.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

An outlier is any value that is more than 1.5 times the interquartile range above the third quartile or below the first quartile. Ignore null values.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@number_of_outliers[number_of_outliers]

"number_of_outliers" is an integer representing the total number of outliers detected under the conditions specified in the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
