# DABench Task 180 - Perform outlier detection on the fare variable for each passenger class separately. Use the Z-score method and determine the number of outliers in each class.

## Task Description

Perform outlier detection on the fare variable for each passenger class separately. Use the Z-score method and determine the number of outliers in each class.

## Concepts

Outlier Detection

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Validate outliers using the Z-score method with a threshold of 3. Use separate calculations for each passenger class (1, 2, and 3).

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `180`
- `answer`: three key-value pairs separated by spaces: `@class2_outliers[<o2_value>] @class1_outliers[<o1_value>] @class3_outliers[<o3_value>]`

All values are non-negative integers representing outlier counts by class.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
