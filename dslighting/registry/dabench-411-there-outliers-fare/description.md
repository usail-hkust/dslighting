# DABench Task 411 - Are there any outliers in the fare paid by the passengers? If so, how many outliers are there and what is their range?

## Task Description

Are there any outliers in the fare paid by the passengers? If so, how many outliers are there and what is their range?

## Concepts

Outlier Detection

## Data Description

Dataset file: `titanic_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

An outlier is identified based on the IQR method. An outlier is defined as a point that falls outside 1.5 times the IQR above the third quartile or below the first quartile.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include the markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@outlier_range_high[answer3] @outlier_count[answer1]

"answer1" is the number of outliers. "answer3" is the highest value among outliers, rounded to 2 decimal places. (Lowest value is not required by the grader.)

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
