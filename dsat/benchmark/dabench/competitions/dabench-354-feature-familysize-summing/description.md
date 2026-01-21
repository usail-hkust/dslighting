# DABench Task 354 - Create a new feature "FamilySize" by summing the IsAlone column with the number of siblings/spouses and number of parents/children on board.

## Task Description

Create a new feature "FamilySize" by summing the IsAlone column with the number of siblings/spouses and number of parents/children on board.

## Concepts

Feature Engineering

## Data Description

Dataset file: `test_x.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Assume each passenger has at least one sibling/spouse and one parent/child on board, therefore, FamilySize = IsAlone + 1 (for sibling or spouse) + 1 (for parent or child).
Compute the average FamilySize and round to one decimal place.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `354`
- `answer`: `@average_familysize[<avg_family_size>]` where `<avg_family_size>` is a number rounded to one decimal place.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
