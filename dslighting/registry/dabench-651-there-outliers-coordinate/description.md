# DABench Task 651 - 3. Are there any outliers in the Z-coordinate column? If yes, how many outliers are there based on the quartile range method with a threshold of 1.5?

## Task Description

3. Are there any outliers in the Z-coordinate column? If yes, how many outliers are there based on the quartile range method with a threshold of 1.5?

## Concepts

Outlier Detection

## Data Description

Dataset file: `DES=+2006261.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the outliers using the interquartile range (IQR) method, where outliers are defined as observations that fall below Q1 - 1.5*IQR or above Q3 + 1.5*IQR. Do not remove any data while performing the outlier calculation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@outlier_count[outlier_number]

"outlier_number" is an integer representing the number of outliers in the data.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
