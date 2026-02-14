# DABench Task 729 - Does the distribution of GDP per capita adhere to a normal distribution?

## Task Description

Does the distribution of GDP per capita adhere to a normal distribution?

## Concepts

Distribution Analysis

## Data Description

Dataset file: `gapminder_cleaned.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the scipy library's normaltest() function on the "Gdppercap" column. Consider the distribution to be normal if p-value is greater than 0.05.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@distribution_normality[distribution_type]

where "distribution_type" is a string which is either "normal" if condition is met or "not normal" if otherwise.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
