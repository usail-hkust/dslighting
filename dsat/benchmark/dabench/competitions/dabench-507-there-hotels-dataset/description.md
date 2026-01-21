# DABench Task 507 - 2. Are there any hotels in the dataset that have a star rating of 5? If yes, how many hotels have a star rating of 5?

## Task Description

2. Are there any hotels in the dataset that have a star rating of 5? If yes, how many hotels have a star rating of 5?

## Concepts

Distribution Analysis

## Data Description

Dataset file: `hotel_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Count only hotels that have a star rating exactly equal to 5. This count value should be a non-negative integer.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@total_hotels[count]

"count" is a non-negative integer representing the total number of hotels with a star rating of 5.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
