# DABench Task 721 - 3. Find the correlation coefficient between the 'mpg' and 'weight' columns.

## Task Description

3. Find the correlation coefficient between the 'mpg' and 'weight' columns.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `auto-mpg.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between mpg and weight. Round r to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_coefficient[r_value]

where 'r_value' is a number between -1 and 1, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
