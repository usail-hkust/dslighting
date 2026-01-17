# DABench Task 593 - Using feature engineering techniques, create a new feature that represents the waiting time for callers before being answered by an agent as a percentage of the average abandonment time. Then, explore the distribution of this new feature and determine if it adheres to a normal distribution.

## Task Description

Using feature engineering techniques, create a new feature that represents the waiting time for callers before being answered by an agent as a percentage of the average abandonment time. Then, explore the distribution of this new feature and determine if it adheres to a normal distribution.

## Concepts

Feature Engineering, Distribution Analysis

## Data Description

Dataset file: `20170413_000000_group_statistics.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Create a new feature 'waiting_ratio' that is defined as the ratio of average waiting time to the average abandonment time, represented as a percentage. Convert the waiting and abandonment time from format HH:MM:SS to seconds before the calculation. After creating the feature, calculate the skewness of this new feature. Use the skewness to determine whether the data is normally distributed. For normally distributed data, skewness should be about 0.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `593`
- `answer`: `@is_normal[<is_normal>]`, a boolean flag set to `True` if the waiting_ratio feature is approximately normal, otherwise `False`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
