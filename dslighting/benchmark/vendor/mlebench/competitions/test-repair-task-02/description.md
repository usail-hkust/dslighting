# Bike Sharing Demand Prediction

## Description
This competition focuses on predicting bike rental counts using historical weather and temporal data from a bike sharing system. The goal is to forecast the total number of bikes rented (`count`) during each hour based on features like season, weather conditions, temperature, humidity, and time-based indicators. This predictive task is essential for optimizing bike availability, managing inventory, and improving customer satisfaction in urban mobility systems.

## Evaluation
The competition uses **Root Mean Squared Logarithmic Error (RMSLE)** as the evaluation metric.

**Formula:**
```
RMSLE = √(1/n * Σ(log(p_i + 1) - log(a_i + 1))²)
```
Where:
- `p_i` is the predicted count
- `a_i` is the actual count
- `n` is the number of observations
- `log` is the natural logarithm

## Submission Format
Submissions should be a CSV file with two columns: `datetime` and `count`. The predictions must match the datetime values from the test set exactly.

```csv
datetime,count
2011-01-01 01:00:00,50
2011-01-01 02:00:00,40
...
```

## Dataset Description
The dataset contains hourly bike rental data split into training and test sets:
- **Training set**: 6,966 observations with complete features and target variables
- **Test set**: 1,742 observations with features only (target variables to be predicted)

## Data Fields
- `datetime`: Hourly date-time stamp (YYYY-MM-DD HH:MM:SS)
- `season`: Season (1: spring, 2: summer, 3: fall, 4: winter)
- `holiday`: Whether the day is a holiday (0: no, 1: yes)
- `workingday`: Whether the day is a working day (0: no, 1: yes)
- `weather`: Weather situation (1: clear, 2: mist, 3: light precipitation, 4: heavy precipitation)
- `temp`: Temperature in Celsius
- `atemp`: "Feels like" temperature in Celsius
- `humidity`: Relative humidity (%)
- `windspeed`: Wind speed
- `casual`: Number of non-registered user rentals (training set only)
- `registered`: Number of registered user rentals (training set only)
- `count`: Total number of bike rentals (target variable)

**Note**: The test set contains only the first 9 fields (`datetime` through `windspeed`), while the training set includes all 12 fields.