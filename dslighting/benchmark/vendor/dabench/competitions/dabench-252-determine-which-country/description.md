# DABench Task 252 - Determine which country's gross domestic product per capita in the year 1992 had the highest skewness among all countries in the dataset.

## Task Description

Determine which country's gross domestic product per capita in the year 1992 had the highest skewness among all countries in the dataset.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `gapminder_gdp_asia.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use Python's SciPy library to calculate the skewness of each country's gross domestic product per capita in 1992. Skewness should be calculated with Fisher’s definition, i.e. the one that's adjusted for the normal distribution.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `252`
- `answer`: `@highest_skewness_country[<country_name>]` where `<country_name>` is the string result.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
