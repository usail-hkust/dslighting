# DABench Task 177 - Investigate the distribution of ages for each passenger class. Determine if there is a significant difference in the age distributions between the 1st class and 3rd class. Test the difference utilising the Mann-Whitney U test and use 0.05 as the alpha (significance) level. Null ages are not taken into calculation.

## Task Description

Investigate the distribution of ages for each passenger class. Determine if there is a significant difference in the age distributions between the 1st class and 3rd class. Test the difference utilising the Mann-Whitney U test and use 0.05 as the alpha (significance) level. Null ages are not taken into calculation.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
The analysis should only include the 1st and 3rd classes.
Null values in the "Age" column should be ignored.
The "age distribution difference" is determined using a Mann-Whitney U test with an alpha (significance) level of 0.05.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `177`
- `answer`: `@significance[<Yes/No>]` indicating whether there is a significant difference.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
