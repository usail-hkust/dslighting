# DABench Task 208 - 2. Calculate the mean and standard deviation of the "compound" sentiment score column.

## Task Description

2. Calculate the mean and standard deviation of the "compound" sentiment score column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `fb_articles_20180822_20180829_df.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean and standard deviation of the 'compound' sentiment score using standard statistical methods. Please use a standard approach and do not use any approximations or assumptions. Note that the 'compound' column contains no missing values according to the scenario information.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `208`
- `answer`: two key-value pairs separated by a space: `@compound_mean[<mean_value>] @compound_std[<std_value>]`

Both values are rounded to three decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
