# DABench Task 217 - Find the site identifier(s) with the highest positive_diffsel value.

## Task Description

Find the site identifier(s) with the highest positive_diffsel value.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `ferret-Pitt-2-preinf-lib2-100_sitediffsel.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Extract the site identifier corresponding to the highest positive_diffsel value.
In the case multiple sites have the same highest positive_diffsel value, list all site identifiers.
Assume the 'positive_diffsel' column contains only unique values unless specified otherwise.}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `217`
- `answer`: `@site_identifier[<site_identifier>]` where `<site_identifier>` is taken from the 'site' column (comma-separated if multiple).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
