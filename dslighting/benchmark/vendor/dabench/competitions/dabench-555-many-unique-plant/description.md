# DABench Task 555 - How many unique plant species (represented by unique SPP_SYMBOL values) are there in the dataset, where each species has at least 5 observations?

## Task Description

How many unique plant species (represented by unique SPP_SYMBOL values) are there in the dataset, where each species has at least 5 observations?

## Concepts

Feature Engineering

## Data Description

Dataset file: `tree.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Count unique SPP_SYMBOL values that appear at least 5 times.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `555`
- `answer`: `@unique_species_count[<species_count>]` where `<species_count>` is an integer.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
