# DABench Task 510 - 2. Which hotel brand has the highest average star rating among hotels with at least 100 reviews?

## Task Description

2. Which hotel brand has the highest average star rating among hotels with at least 100 reviews?

## Concepts

Summary Statistics, Feature Engineering

## Data Description

Dataset file: `hotel_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Only consider hotel brands that have at least 10 hotels in the dataset. Do not include hotels without a brand or without a star rating in the calculation. If there is a tie, return the brand with the largest number of hotels in the dataset. Calculate the average using Arithmetic Mean (Sum of observations / Number of observations).

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@brand_with_highest_average_star_rating[brand_name]

"brand_name" is the name of the hotel brand as a string.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
