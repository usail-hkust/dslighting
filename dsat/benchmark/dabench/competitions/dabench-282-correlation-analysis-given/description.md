# DABench Task 282 - Perform correlation analysis on the given dataset to determine if there is any relationship between the Agri and Residential columns. Additionally, explore the distribution of the Agri column and identify any outliers using z-score as the outlier detection method. Treat any value which has z-score above 3 as an outlier.

## Task Description

Perform correlation analysis on the given dataset to determine if there is any relationship between the Agri and Residential columns. Additionally, explore the distribution of the Agri column and identify any outliers using z-score as the outlier detection method. Treat any value which has z-score above 3 as an outlier.

## Concepts

Correlation Analysis, Distribution Analysis, Outlier Detection

## Data Description

Dataset file: `veracruz 2016.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient to assess the linear relationship between Agri and Residential columns. Treat a value as an outlier if the z-score is above 3. Do not consider any other method for outlier detection. Use scipy's pearsonr method for correlation calculation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `282`
- `answer`: two key-value pairs separated by a space: `@number_of_outliers[<number_of_outliers>] @correlation_coefficient[<r_value>]`

`<r_value>` is between -1 and 1 (two decimals); `<number_of_outliers>` is an integer count of Agri outliers.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
