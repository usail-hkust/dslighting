# DABench Task 572 - Identify the date with the highest closing value of the S&P 500 Index (.SPX). Calculate the percentage change in the stock price of Apple Inc. (AAPL) from its closing price on the previous day to its closing price on the identified date.

## Task Description

Identify the date with the highest closing value of the S&P 500 Index (.SPX). Calculate the percentage change in the stock price of Apple Inc. (AAPL) from its closing price on the previous day to its closing price on the identified date.

## Concepts

Summary Statistics, Correlation Analysis

## Data Description

Dataset file: `tr_eikon_eod_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

1. The date where the S&P 500 Index (.SPX) reached its maximum value should be identified.
2. The percentage change is calculated as: ((price on identified date / price on previous day) - 1) * 100.
3. Percentage change should be calculated only if the previous day data exists. If the identified date is the first date in the dataset, state that the previous day data doesn't exist.
4. The data for the previous day is defined as the data on the date immediately preceding the identified date when sorting the dates in ascending order. Hunting for the "previous" trading day is not required.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `572`
- `answer`: two key-value pairs separated by a space: `@max_SPX_date[<date>] @AAPL_price_percentage_change[<percentage_change>]`

`<date>` is `YYYY-MM` or `YYYY-MM-DD` as in the data, and `<percentage_change>` is a number to two decimals (or the string "Previous day data doesn't exist" if applicable).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
