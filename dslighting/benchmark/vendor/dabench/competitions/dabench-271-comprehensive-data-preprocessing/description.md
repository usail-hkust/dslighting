# DABench Task 271 - Perform comprehensive data preprocessing for the dataset by:
1. Removing any duplicate entries.
2. Filling in missing values in the USFLUX column with the mean value of the column.
3. Transforming the MEANJZH column by applying the logarithm function (base 10).
4. Normalizing the TOTUSJZ column using Min-Max normalization.

## Task Description

Perform comprehensive data preprocessing for the dataset by:
1. Removing any duplicate entries.
2. Filling in missing values in the USFLUX column with the mean value of the column.
3. Transforming the MEANJZH column by applying the logarithm function (base 10).
4. Normalizing the TOTUSJZ column using Min-Max normalization.

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `3901.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

When applying the logarithm function, add a small constant (1e-10) to the MEANJZH column to avoid infinity. The Min-Max normalization needs to transform the TOTUSJZ values to the range 0 to 1.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `271`
- `answer`: three key-value pairs separated by spaces: `@norm_TOTUSJZ[<value>] @log_MEANJZH[<value>] @clean_entries[<value>]`

`norm_TOTUSJZ` and `log_MEANJZH` are rounded to three decimals; `clean_entries` is the count after cleaning duplicates.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
