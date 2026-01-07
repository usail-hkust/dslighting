# DABench Task 514 - 3. What is the average review count for hotels in each city? Are there any cities where the average review count is significantly higher or lower compared to the overall average review count of all hotels?

## Task Description

3. What is the average review count for hotels in each city? Are there any cities where the average review count is significantly higher or lower compared to the overall average review count of all hotels?

## Concepts

Summary Statistics, Distribution Analysis

## Data Description

Dataset file: `hotel_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the average review count for each city. Compare the results to the overall average review count. Report cities where the average review count is more or less than twice the overall average.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@higher_city_count[number_of_higher_cities] @lower_city_count[number_of_lower_cities]

"number_of_higher_cities" and "number_of_lower_cities" are positive integers representing the number of cities meeting the corresponding criteria.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
