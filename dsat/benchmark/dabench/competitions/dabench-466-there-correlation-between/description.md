# DABench Task 466 - 3. Is there a correlation between the count of offenses and the age of the offender?

## Task Description

3. Is there a correlation between the count of offenses and the age of the offender?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `arrest_expungibility.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between count and age. Ignore the null values in the 'Count' column for this analysis. A value of r below -0.6 or above +0.6 indicates a strong correlation, between -0.6 and -0.3 or between +0.3 and +0.6 indicates a moderate correlation, -0.3 and +0.3 indicates a weak correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_strength[strength]

"strength" is a string which can be "strong", "moderate", or "weak" based on the criteria provided in the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
