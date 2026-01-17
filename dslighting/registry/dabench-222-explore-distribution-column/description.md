# DABench Task 222 - Explore the distribution of the abs_diffsel column and determine if it adheres to a normal distribution by calculating skewness and kurtosis. The skewness and kurtosis values should be calculated using Fisher’s method. If the skewness value is between -0.5 and 0.5, the data is fairly symmetrical. If the kurtosis value is around 0, then a normal distribution is often assumed.

## Task Description

Explore the distribution of the abs_diffsel column and determine if it adheres to a normal distribution by calculating skewness and kurtosis. The skewness and kurtosis values should be calculated using Fisher’s method. If the skewness value is between -0.5 and 0.5, the data is fairly symmetrical. If the kurtosis value is around 0, then a normal distribution is often assumed.

## Concepts

Distribution Analysis, Feature Engineering

## Data Description

Dataset file: `ferret-Pitt-2-preinf-lib2-100_sitediffsel.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Perform the calculations using non-parametric methods, specifically the skew and kurtosis functions provided in the scipy.stats module of Python. All numeric values should be rounded to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `222`
- `answer`: `@skewness_value[<skewness_value>]` where `<skewness_value>` is a float between -0.5 and 0.5, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
