# DABench Task 219 - Identify the site(s) with outliers in the abs_diffsel column using the interquartile range (IQR) method. An outlier is defined as a value that is below Q1 - 1.5*IQR or above Q3 + 1.5*IQR. Provide the site identifier(s) and the corresponding absolute difference in selection values for the outliers.

## Task Description

Identify the site(s) with outliers in the abs_diffsel column using the interquartile range (IQR) method. An outlier is defined as a value that is below Q1 - 1.5*IQR or above Q3 + 1.5*IQR. Provide the site identifier(s) and the corresponding absolute difference in selection values for the outliers.

## Concepts

Outlier Detection

## Data Description

Dataset file: `ferret-Pitt-2-preinf-lib2-100_sitediffsel.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the interquartile range (IQR) method for outlier detection. Calculate the IQR as the difference between the first quartile (Q1) and the third quartile (Q3) of the abs_diffsel column. Consider a value as an outlier if it is below Q1 - 1.5*IQR or above Q3 + 1.5*IQR.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `219`
- `answer`: two key-value pairs separated by a space: `@outlier_values[<value1,value2,...>] @site_identifiers[<site_id1,site_id2,...>]`

`<site_id>` entries are the identifiers with detected outliers; `<value>` entries are the corresponding absolute differences (two decimals), both comma-separated.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
