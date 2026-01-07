# DABench Task 655 - 1. Perform a correlation analysis on the X, Y, and Z coordinate columns. Calculate the Pearson correlation coefficients between the X and Y coordinates, and between the X and Z coordinates.

## Task Description

1. Perform a correlation analysis on the X, Y, and Z coordinate columns. Calculate the Pearson correlation coefficients between the X and Y coordinates, and between the X and Z coordinates.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `DES=+2006261.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the correlation coefficient (r) to assess the strength and direction of the linear relationship between the pairs of variables.
Report the correlation coefficients for both pairs.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@correlation_XZ[r_value_XZ] @correlation_XY[r_value_XY]

"r_value_XY" and "r_value_XZ" are numbers between -1 and 1, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
