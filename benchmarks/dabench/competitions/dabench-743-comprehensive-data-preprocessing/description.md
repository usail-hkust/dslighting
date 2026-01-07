# DABench Task 743 - Perform a comprehensive data preprocessing on the Credit.csv file by handling missing values in the "Education" column using imputation with the most frequent value, and normalizing the "Income" and "Balance" columns.

## Task Description

Perform a comprehensive data preprocessing on the Credit.csv file by handling missing values in the "Education" column using imputation with the most frequent value, and normalizing the "Income" and "Balance" columns.

## Concepts

Comprehensive Data Preprocessing, Feature Engineering

## Data Description

Dataset file: `Credit.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
First, no assumptions should be made about the presence of missing values in the Education column. Check first if there are any such values even though the scenario information states that there are none.
For missing value imputation, use the mode (most frequently occurring value) to fill the missing gaps in the Education column.
For normalization of "Income" and "Balance", use Min-Max normalization method whose calculation is given by: (X - min(X)) / (max(X) - min(X)) where X denotes a value from the respective column.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@income_normalization[income_min_val, income_max_val]

Quote the `answer` cell (as in the sample) to preserve the comma-separated values. "income_min_val" and "income_max_val" are the minimum and maximum values of the "Income" column before normalization, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
