# Playground Series S3E11

## Description

Welcome to Playground Series Season 3, Edition 11! This is part of our Tabular Tuesday competitions in March 2023. Each competition runs for 2 weeks and uses synthetically-generated datasets from real-world data.

This edition uses a dataset generated from the Media Campaign Cost Prediction dataset, providing opportunities for rapid experimentation with models and feature engineering.

## Evaluation

**Root Mean Squared Log Error (RMSLE)**

Submissions are scored on RMSLE (sklearn `mean_squared_log_error` with `squared=False`).

## Submission Format

For each id in the test set, you must predict the value for cost:

```
id,cost
360336,99.615
360337,87.203
...
```

## Dataset Description

The dataset (both train and test) was generated from a deep learning model trained on the Media Campaign Cost Prediction dataset. Feel free to use the original dataset as part of this competition.

## Files

- `train.csv`: Training dataset; cost is the target
- `test.csv`: Test dataset
- `sample_submission.csv`: Sample submission in correct format
