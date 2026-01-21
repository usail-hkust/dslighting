# DABench Task 574 - Perform data preprocessing on the stock prices of Microsoft Corporation (MSFT), SPDR S&P 500 ETF Trust (SPY), and the CBOE Volatility Index (.VIX). This preprocessing includes removing missing values, normalizing the data, and encoding any categorical variables. Calculate the correlation matrix between the preprocessed stock prices.

## Task Description

Perform data preprocessing on the stock prices of Microsoft Corporation (MSFT), SPDR S&P 500 ETF Trust (SPY), and the CBOE Volatility Index (.VIX). This preprocessing includes removing missing values, normalizing the data, and encoding any categorical variables. Calculate the correlation matrix between the preprocessed stock prices.

## Concepts

Comprehensive Data Preprocessing, Correlation Analysis

## Data Description

Dataset file: `tr_eikon_eod_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

1. Missing values should be removed entirely from the dataset.
2. The normalization method to be used is feature scaling (rescaling the data to range between 0 and 1).
3. For categorical variables, use one hot encoding method, though no categorical data exists in the provided price columns.
4. The correlation computation method to be used is Pearson's correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `574`
- `answer`: three key-value pairs separated by spaces: `@MSFT_VIX_correlation[<correlation>] @SPY_VIX_correlation[<correlation>] @MSFT_SPY_correlation[<correlation>]`

Each `<correlation>` is a number between -1 and 1 (two decimals).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
