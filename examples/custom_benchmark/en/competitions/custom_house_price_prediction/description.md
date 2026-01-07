# House Price Prediction Challenge

## Task

Predict the sale price (USD) for a given house. This is a regression task that estimates market price from features such as area, rooms, and location.

## Data

### Files
- `train.csv` - training data with features and actual price
- `sample_submission.csv` - submission format example

### Feature columns

| Column | Type | Description | Range |
|------|------|------|------|
| `house_id` | int | Unique house ID | 1 - N |
| `area` | int | Living area (sqft) | 800 - 3500 |
| `bedrooms` | int | Bedroom count | 1 - 5 |
| `age` | int | House age (years) | 0 - 50 |
| `location_score` | int | Location score | 1 - 10 |
| `price` | float | Sale price (USD) | Train set only |

## Submission format

The submission must be CSV with the following columns:

```csv
house_id,predicted_price
1,250000.00
2,350000.00
...
```

- `house_id`: house ID (matches the test set)
- `predicted_price`: predicted price (float)

## Metric

**Scoring**: RMSE (Root Mean Squared Error)

```
RMSE = sqrt(mean((predicted_price - actual_price)^2))
```

- **Lower is better**: RMSE of 0 means a perfect prediction.
- Predictions are compared to the private test labels.

## Goal

Minimize RMSE between predicted and actual prices to build the most accurate model.

## Difficulty

**Medium** - good for practicing regression and feature engineering
