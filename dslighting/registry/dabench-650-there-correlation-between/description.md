# DABench Task 650 - 2. Is there any correlation between the X-coordinate and Y-coordinate columns? If so, what is the correlation coefficient?

## Task Description

2. Is there any correlation between the X-coordinate and Y-coordinate columns? If so, what is the correlation coefficient?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `DES=+2006261.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Pearson Correlation Coefficient to find the correlation between the X and Y coordinates. Round the calculated correlation coefficient to three decimal places. If the absolute correlation coefficient is less than 0.05, assume the correlation is negligible and consider the correlation value as zero.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_coefficient[correlation_coefficient_value]

"correlation_coefficient_value" is a decimal number between -1 and 1, rounded to three decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
