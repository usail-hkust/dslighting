# DABench Task 69 - Perform feature engineering by creating a new feature called "experience_score" that is calculated by multiplying the exper column with the looks column. Then, calculate the Pearson correlation coefficient between the "experience_score" feature and the wage column.

## Task Description

Perform feature engineering by creating a new feature called "experience_score" that is calculated by multiplying the exper column with the looks column. Then, calculate the Pearson correlation coefficient between the "experience_score" feature and the wage column.

## Concepts

Feature Engineering, Correlation Analysis

## Data Description

Dataset file: `beauty and the labor market.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Create "experience_score" by directly multiplying values of exper and looks column. Calculate Pearson correlation coefficient between the new feature "experience_score" and wage. Correlation should be calculated up to three decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `69`
- `answer`: `@correlation[<correlation>]` where `<correlation>` is the coefficient rounded to three decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
