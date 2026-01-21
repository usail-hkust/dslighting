# DABench Task 209 - 3. Is there any correlation between the "neg" and "pos" sentiment score columns? If so, what is the correlation coefficient?

## Task Description

3. Is there any correlation between the "neg" and "pos" sentiment score columns? If so, what is the correlation coefficient?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `fb_articles_20180822_20180829_df.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between 'neg' and 'pos' sentiment scores. If the Pearson correlation coefficient (absolute value) is close to 1, it means that there exists a strong correlation. If it is close to 0, it means that there exists a weak or no correlation. If the coefficient is positive, the correlation is positive; if negative, the correlation is negative.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `209`
- `answer`: `@correlation_coefficient[<r_value>]` where `<r_value>` is between -1 and 1, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
