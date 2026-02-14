# DABench Task 359 - Check if the distribution of wind speed in the weather dataset is skewed.

## Task Description

Check if the distribution of wind speed in the weather dataset is skewed.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `weather_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

For missing values in the "wind speed" column, use the 'dropna' method to remove these data points before calculations.
Determine the skewness using Pearson's First Coefficient of Skewness. 
Report whether the distribution is positively skewed, negatively skewed, or symmetric based on the obtained skewness value. 
Assume the distribution to be positively skewed if skewness value is > 0, negatively skewed if skewness is < 0, and symmetric if skewness is 0.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `359`
- `answer`: two key-value pairs separated by a space: `@skewness_value[<skew_value>] @skewness_type[<type_value>]`

`<skew_value>` is a float rounded to two decimals. `<type_value>` is `positive`, `negative`, or `symmetric`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
