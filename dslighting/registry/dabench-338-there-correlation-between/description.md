# DABench Task 338 - 3. Is there a correlation between the size rank of a region and the median sold price per square foot? If yes, is it a positive or negative correlation?

## Task Description

3. Is there a correlation between the size rank of a region and the median sold price per square foot? If yes, is it a positive or negative correlation?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `Zip_MedianSoldPricePerSqft_AllHomes.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation between the variables size rank and median sold price per square foot, considering only non-null values. A correlation value > 0 indicates a positive correlation, while a value < 0 indicates a negative correlation. A correlation value close to zero indicates no correlation. Calculate the correlation coefficient up to three decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `338`
- `answer`: two key-value pairs separated by a space: `@correlation_type[<correlation_type>] @correlation_coefficient[<correlation_coefficient>]`

`<correlation_coefficient>` is between -1 and 1 (three decimals). `<correlation_type>` is `Positive Correlation`, `Negative Correlation`, or `No Correlation`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
