# DABench Task 465 - 2. Is the distribution of offender ages normally distributed or skewed?

## Task Description

2. Is the distribution of offender ages normally distributed or skewed?

## Concepts

Distribution Analysis

## Data Description

Dataset file: `arrest_expungibility.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate skewness of the 'Age' column using the skew function from the 'scipy.stats'. A skewness value between -0.5 to +0.5 indicates that the distribution is approximately symmetric, a skewness value greater than +0.5 indicates a distribution skewed to the right and a skewness value less than -0.5 indicates a distribution skewed to the left.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@distribution_skew[skewness]

"skewness" is "symmetric", "skewed_right", or "skewed_left" based on the criteria provided in the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
