# Demand Forecasting - Kernels Only

## Description

This competition is provided as a way to explore different time series techniques on a relatively simple and clean dataset. You are given 5 years of store-item sales data and asked to predict 3 months of sales for 50 different items at 10 different stores.

What's the best way to deal with seasonality? Should stores be modeled separately, or can you pool them together? This is a great competition to explore different models and improve your skills in forecasting.

## Evaluation

Submissions are evaluated on **SMAPE** (Symmetric Mean Absolute Percentage Error) between forecasts and actual values.

$$\text{SMAPE} = \frac{100}{n}\sum_{i=1}^{n}\frac{|y_i - \hat{y}_i|}{|y_i| + |\hat{y}_i|}$$

We define SMAPE = 0 when both the actual and predicted values are 0.

## Submission Format

For each id in the test set, you must predict a probability for the sales variable:

```
id,sales
0,35
1,22
2,5
...
```

## Dataset Description

The objective is to predict 3 months of item-level sales data at different store locations.

## Data Fields

- `date`: Date of the sale data (no holiday effects or store closures)
- `store`: Store ID
- `item`: Item ID
- `sales`: Number of items sold at a particular store on a particular date

## Files

- `train.csv`: Training data (5 years)
- `test.csv`: Test data (3 months, Public/Private split is time based)
- `sample_submission.csv`: Sample submission in correct format
