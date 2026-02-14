# DABench Task 254 - Identify any outliers in the gross domestic product per capita data for the year 1982 for all countries. Define an outlier as any data point that falls more than 1.5 times the interquartile range (IQR) below the first quartile or above the third quartile. Report the country or countries which their gdpPercap_1982 values are identified as outliers.

## Task Description

Identify any outliers in the gross domestic product per capita data for the year 1982 for all countries. Define an outlier as any data point that falls more than 1.5 times the interquartile range (IQR) below the first quartile or above the third quartile. Report the country or countries which their gdpPercap_1982 values are identified as outliers.

## Concepts

Outlier Detection

## Data Description

Dataset file: `gapminder_gdp_asia.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the interquartile range (IQR) rule for outlier detection: a data point is considered an outlier if it falls more than 1.5*IQR below the first quartile (Q1) or above the third quartile (Q3). Don't use any other outlier detection methods or parameters.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `254`
- `answer`: `@outlier_countries[<list_of_strings>]` where `<list_of_strings>` is a comma-separated list of outlier country names (IQR rule).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
