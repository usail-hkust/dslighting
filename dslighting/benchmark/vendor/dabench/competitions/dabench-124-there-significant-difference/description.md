# DABench Task 124 - Is there a significant difference in the total number of vaccinations administered per hundred people between countries that use different vaccines?

## Task Description

Is there a significant difference in the total number of vaccinations administered per hundred people between countries that use different vaccines?

## Concepts

Summary Statistics, Correlation Analysis

## Data Description

Dataset file: `country_vaccinations.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Only consider countries using Pfizer/BioNTech, Moderna, Oxford/AstraZeneca, and Johnson&Johnson/Janssen. 
The country must have data without null values in the column of total vaccinations per hundred people.
Use One-Way Analysis of Variance (ANOVA) to test if there's significant difference among different vaccine groups. 
Consider the differences among vaccine groups to be significant if the p-value is less than 0.05.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `124`
- `answer`: `@significance_of_difference[<significance>]` where `<significance>` is `yes` or `no`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
