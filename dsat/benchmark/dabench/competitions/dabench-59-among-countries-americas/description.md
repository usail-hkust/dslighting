# DABench Task 59 - Among the countries in the "Americas" region, which country has the highest average number of cases recorded over the years?

## Task Description

Among the countries in the "Americas" region, which country has the highest average number of cases recorded over the years?

## Concepts

Distribution Analysis, Summary Statistics, Feature Engineering

## Data Description

Dataset file: `estimated_numbers.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the average of "No. of cases" for each country in the "Americas" region and report the country with the highest average number of cases. Count only complete years, i.e., exclude years with missing data.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `59`
- `answer`: `@country_name[<country>]` where `<country>` is the country name with the highest average cases.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
