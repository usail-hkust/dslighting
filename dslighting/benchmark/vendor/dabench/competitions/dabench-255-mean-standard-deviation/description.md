# DABench Task 255 - Calculate the mean and standard deviation of the gross domestic product per capita in the year 2007 for all countries in the dataset. Round your answers to 2 decimal places.

## Task Description

Calculate the mean and standard deviation of the gross domestic product per capita in the year 2007 for all countries in the dataset. Round your answers to 2 decimal places.

## Concepts

Summary Statistics

## Data Description

Dataset file: `gapminder_gdp_asia.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Perform arithmetic mean and standard deviation calculations on the 'gdpPercap_2007' column of the dataset. Round your answer to two decimal places. Do not use modes, medians, or any other form of average.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `255`
- `answer`: two key-value pairs separated by a space: `@standard_deviation_gdp2007[<float>] @mean_gdp2007[<float>]`

Each value is a positive number rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
