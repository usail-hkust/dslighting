# DABench Task 513 - 2. Among the hotels with a star rating, what is the correlation between the number of reviews a hotel has received and its bubble score? Do hotels with higher star ratings tend to have higher bubble scores and more reviews?

## Task Description

2. Among the hotels with a star rating, what is the correlation between the number of reviews a hotel has received and its bubble score? Do hotels with higher star ratings tend to have higher bubble scores and more reviews?

## Concepts

Correlation Analysis, Distribution Analysis

## Data Description

Dataset file: `hotel_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the correlation coefficient using the Pearson method. Consider only non-null values. Report the correlation separately for hotels with star ratings below 3, between 3 and 4, and above 4.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@above4_correlation[correlation_value3] @below3_correlation[correlation_value1] @between3and4_correlation[correlation_value2]

Each "correlation_value" is a float between -1 and 1, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
