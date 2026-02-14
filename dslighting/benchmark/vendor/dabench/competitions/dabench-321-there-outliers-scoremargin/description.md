# DABench Task 321 - Are there any outliers in the SCOREMARGIN column? If so, how many?

## Task Description

Are there any outliers in the SCOREMARGIN column? If so, how many?

## Concepts

Outlier Detection

## Data Description

Dataset file: `0020200722.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

You should use the IQR method to define an outlier. An observation is considered an outlier if it lies 1.5 IQR below the first quartile or 1.5 IQR above the third quartile. Since SCOREMARGIN contains string values, first convert the SCOREMARGIN data into integer or float and then clean the data by ignoring any non-numeric characters or punctuation marks.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `321`
- `answer`: `@outlier_count[<count>]` where `<count>` is an integer number of outliers detected using the IQR method.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
