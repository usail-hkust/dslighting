# DABench Task 552 - Are the HT_M column and the BA_M2 column correlated?

## Task Description

Are the HT_M column and the BA_M2 column correlated?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `tree.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between the 'HT_M' and 'BA_M2' columns. The answer should be rounded to the third decimal place. Consider the relationship to be linear if the absolute value of r is greater than or equal to 0.5. Consider the relationship to be non-linear if the absolute value of r is less than 0.5.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `552`
- `answer`: two key-value pairs separated by a space: `@relationship_type[<relationship_type>] @correlation_coefficient[<r_value>]`

`<r_value>` is a float between -1 and 1 (three decimals); `<relationship_type>` is `linear` or `nonlinear`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
