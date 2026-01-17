# DABench Task 736 - Create a new feature by combining the population and GDP per capita columns. Normalize this new feature to a range of [0, 1]. Then, conduct a distribution analysis on this normalized feature and determine if it adheres to a normal distribution.

## Task Description

Create a new feature by combining the population and GDP per capita columns. Normalize this new feature to a range of [0, 1]. Then, conduct a distribution analysis on this normalized feature and determine if it adheres to a normal distribution.

## Concepts

Feature Engineering, Distribution Analysis

## Data Description

Dataset file: `gapminder_cleaned.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Define the new feature as population multiplied by GDP per capita. Normalize this new feature by applying min-max scaling. Perform a Shapiro-Wilk test to determine if the normalized feature follows a normal distribution. Consider the data to follow a normal distribution if the p-value of the Shapiro-Wilk test is greater than 0.05.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@is_normal[is_normal]

where "is_normal" is a string that can be either "yes" or "no", indicating whether the normalized feature follows a normal distribution.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
