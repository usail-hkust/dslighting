# Bike Sharing Demand Prediction

## Description
Predict bike rental counts based on temporal, weather, and seasonal features using historical rental data from a bike sharing system. The goal is to forecast the total number of bikes rented (`count`) during each hour period, which is crucial for inventory management, station planning, and optimizing bike redistribution strategies.

## Evaluation
The competition uses **Root Mean Squared Logarithmic Error (RMSLE)** as the evaluation metric:

```
RMSLE = sqrt(1/n * Σ(log(p_i + 1) - log(a_i + 1))²)
```

Where:
- `p_i` is the predicted count
- `a_i` is the actual count
- `n` is the number of observations
- `log` is the natural logarithm

This metric is robust to outliers and penalizes underestimates more than overestimates, which is important for business planning.

## Submission Format
Submissions should be a CSV file with two columns: `datetime` and `count`. The file should contain predictions for all instances in the test set.

```csv
datetime,count
2011-07-19 11:00:00,127
2011-07-19 12:00:00,89
2012-01-16 00:00:00,13
...
```

## Dataset Description
The dataset contains hourly bike rental data split into training and test sets:
- **Training set**: 5,000 hourly records with complete features and target variables
- **Test set**: 2,178 hourly records with features only (targets provided separately for validation)

## Data Fields
- `datetime`: Hourly date + timestamp (format: YYYY-MM-DD HH:MM:SS)
- `season`: Season (1: spring, 2: summer, 3: fall, 4: winter)
- `holiday`: Whether day is holiday (1: holiday, 0: not holiday)
- `workingday`: Whether day is a working day (1: working day, 0: weekend/holiday)
- `weather`: Weather situation (1: clear, 2: mist, 3: light rain/snow, 4: heavy rain/snow)
- `temp`: Temperature in Celsius
- `atemp`: "Feels like" temperature in Celsius
- `humidity`: Relative humidity (%)
- `windspeed`: Wind speed
- `casual`: Number of non-registered user rentals (training set only)
- `registered`: Number of registered user rentals (training set only)
- `count`: Total number of bike rentals (target variable)

The training set contains all fields, while the test set excludes `casual`, `registered`, and `count` columns.