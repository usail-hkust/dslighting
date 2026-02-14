# Playground Series S3E1

## Description

Welcome to 2023 Playground Series! This is Season 3, Edition 1 - the first of our Tabular Tuesday competitions. These are week-long, lightweight challenges using synthetically-generated datasets from real-world data.

This edition uses a dataset generated from the California Housing Dataset. The goal is to provide an opportunity to quickly iterate through various model and feature engineering ideas.

## Evaluation

**Root Mean Squared Error (RMSE)**

$$\textrm{RMSE} = \sqrt{ \frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2 }$$

## Submission Format

For each id in the test set, you must predict the value for MedHouseVal:

```
id,MedHouseVal
37137,2.01
37138,0.92
...
```

## Dataset Description

The dataset (both train and test) was generated from a deep learning model trained on the California Housing Dataset. Feature distributions are close to, but not exactly the same, as the original.

## Files

- `train.csv`: Training dataset; MedHouseVal is the target
- `test.csv`: Test dataset
- `sample_submission.csv`: Sample submission in correct format
