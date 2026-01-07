# DABench Task 527 - What is the average age of male passengers in each passenger class? How does it compare to the average age of female passengers in each passenger class?

## Task Description

What is the average age of male passengers in each passenger class? How does it compare to the average age of female passengers in each passenger class?

## Concepts

Summary Statistics, Distribution Analysis

## Data Description

Dataset file: `titanic_test.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Determine the average age by using all the non-null age data for male and female passengers in each passenger class. Use the arithmetic mean formula for your calculation. The output should include the average age for males and females in each of passenger classes 1, 2, and 3.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `527`
- `answer`: six key-value pairs separated by spaces: `@average_age_male_class1[<age>] @average_age_male_class2[<age>] @average_age_male_class3[<age>] @average_age_female_class1[<age>] @average_age_female_class2[<age>] @average_age_female_class3[<age>]`

Each `<age>` is a number rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
