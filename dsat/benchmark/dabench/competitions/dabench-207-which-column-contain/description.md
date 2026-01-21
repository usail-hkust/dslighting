# DABench Task 207 - 1. Which column(s) contain missing values in the dataset?

## Task Description

1. Which column(s) contain missing values in the dataset?

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `fb_articles_20180822_20180829_df.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

This question requires a straightforward identification of columns with missing values in the dataset. Only count the missing values in columns where the data type is 'object' (i.e., strings). Do not include columns of other data types and consider a "missing value" as one that is recorded as 'NaN', 'na', 'null', or an empty string in the dataset.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `207`
- `answer`: `@missing_columns_in_object_type[<col1, col2, ...>]` listing the column names with missing values, comma-separated (no duplicates, alphabetical).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
