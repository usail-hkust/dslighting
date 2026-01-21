# DABench Task 496 - Perform feature engineering by creating a new feature called "STEM" (Science, Technology, Engineering, and Math). It should be the sum of the percentages of graduates in the fields of Computer Science, Engineering, Math and Statistics, and Physical Sciences. Calculate the mean and range (maximum - minimum) of the "STEM" feature for the years beyond 2000.

## Task Description

Perform feature engineering by creating a new feature called "STEM" (Science, Technology, Engineering, and Math). It should be the sum of the percentages of graduates in the fields of Computer Science, Engineering, Math and Statistics, and Physical Sciences. Calculate the mean and range (maximum - minimum) of the "STEM" feature for the years beyond 2000.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `percent-bachelors-degrees-women-usa.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the new feature "STEM" as the sum of the percentages of graduates in the fields of Computer Science, Engineering, Math and Statistics, and Physical Sciences.
Compute the mean and the range (maximum - minimum) of the "STEM" feature for the years 2000 and beyond. Round to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

@mean_STEM[mean_value]
@range_STEM[range_value]
where "mean_value" is a floating point number rounded to two decimal places representing the mean of the "STEM" feature.
where "range_value" is a floating point number rounded to two decimal places representing the range of the "STEM" feature.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
