# Predictive Analysis of Bike Sharing Demand Patterns and Environmental Influences

This study presents a comprehensive analysis of bike-sharing demand patterns using a dataset spanning 8,708 hourly records from January 2011 to December 2012. The investigation reveals significant temporal patterns, environmental dependencies, and user behavior characteristics that collectively explain 191.6±181.0 daily rentals. Key findings demonstrate strong seasonal variations, temperature optimization effects, and distinct user segmentation between casual and registered riders.

## 1. Materials and Processing

### 1.1 Dataset Profile
| Metric | Value |
|--------|-------|
| Total Records | 8,708 |
| Date Range | 2011-01-01 to 2012-12-19 |
| Features | 12 (datetime, weather, temporal, user metrics) |
| Missing Values | 0% |
| Target Variable | Count (bike rentals per hour) |

### 1.2 Feature Engineering Strategy
- **Temporal Decomposition**: Extracted hour, dayofweek, month, year from datetime
- **Temperature Optimization**: Binned temperature into optimal ranges (32.96-36.98°C)
- **User Segmentation**: Separated casual vs registered user patterns
- **Weather Classification**: Categorized weather conditions (1-4 scale)
- **Log Transformation**: Applied to target variable to address right-skewness (skewness reduced from 1.24 to -0.85)

## 2. Results and Analysis

### 2.1 Exploratory Visualizations

![Figure 1: Temporal Demand Patterns](./visualizations/temporal_patterns.png)

> **Insight 1:** Temporal analysis reveals pronounced diurnal patterns with peak demand at 17:00 (462.2 rentals) and minimum at 04:00 (6.5 rentals), representing a 455.7-bike amplitude. Monthly patterns show summer peak (June: 242.0 rentals) and winter trough (January: 91.6 rentals). Year-over-year growth of 65.0% indicates rapid system adoption (2011: 144.5 vs 2012: 238.4 rentals).

![Figure 2: Weather Impact Analysis](./visualizations/weather_impact.png)

> **Insight 2:** Environmental factors demonstrate significant predictive power. Temperature shows moderate positive correlation (r=0.390) with optimal range of 32.96-36.98°C yielding 347.1 rentals. Humidity exhibits negative correlation (r=-0.318) with demand reduction of 72.8% above 80% humidity. Weather condition 1 (clear) generates 205.6 rentals versus 118.5 for condition 3 (light rain/snow), representing a 42.3% reduction.

![Figure 3: Correlation Structure](./visualizations/correlation_matrix.png)

> **Insight 3:** Correlation analysis identifies registered users as the strongest predictor (r=0.971), highlighting the importance of user segmentation. High multicollinearity exists between temperature and apparent temperature (r=0.985), suggesting feature reduction potential. The weak windspeed correlation (r=0.099) indicates limited predictive value for this variable.

![Figure 4: User Behavior Patterns](./visualizations/workday_holiday_analysis.png)

> **Insight 4:** User segmentation reveals distinct behavioral patterns. Registered users dominate overall composition (81.2%) with peak usage at 17:00 (386.7 users). Casual users show 132.0% weekend growth versus registered users' 23.2% decline, indicating complementary usage patterns. Workdays exhibit registered user dominance (168.2 vs 25.1 casual), while weekends show more balanced distribution.

## 3. Discussion and Insights

The analysis reveals three critical demand drivers: (1) temporal patterns accounting for commuting behaviors, (2) environmental optimization with temperature thresholds, and (3) user segmentation explaining 97.1% of variance through registered user patterns. The right-skewed distribution (mean: 191.6, std: 181.0) suggests zero-inflated or Poisson regression approaches may be appropriate.

Notable anomalies include the unexpected performance of weather condition 4 (164.0 rentals) exceeding condition 3 (118.5 rentals), potentially indicating data quality issues or special circumstances. The weekend vs weekday similarity (188.5 vs 192.8 rentals) masks important compositional differences revealed through user segmentation.

## 4. Recommendations

1. **Modeling Strategy**: Implement gradient boosting with temporal features, temperature optimization bins, and user segmentation as primary predictors
2. **Feature Selection**: Exclude windspeed due to weak correlation (r=0.099) and address temperature/apparent temperature multicollinearity
3. **Data Transformation**: Apply log transformation to target variable to normalize distribution
4. **Validation Approach**: Use temporal cross-validation to account for seasonality and growth trends
5. **Business Applications**: Optimize bike redistribution based on time-of-day patterns and weather forecasts, with special attention to temperature and humidity thresholds


# Technical Solution Report: bike-sharing-demand

## 1. Performance Statistics

| Attribute | Result Value | Unit/Type |
| :--- | :--- | :--- |
| **Evaluation Score** | **0.3482** | Metric-Specific |
| **Compute Resources** | `$0.0245` | USD |

## 2. Methodology and Implementation Details

Ensemble-Free Random Forest Regression with Temporal Feature Engineering for Bike-Sharing Demand Forecasting

This study presents a predictive modeling approach for the bike-sharing demand forecasting task, utilizing a single Random Forest Regressor. The core methodological contributions are the comprehensive engineering of temporal features from datetime stamps and the application of cyclical encoding to capture periodic patterns. The model is trained to predict the total hourly rental count, with predictions post-processed to ensure non-negativity and integer values. Validation results indicate a baseline level of performance, establishing a foundation for more complex ensemble methods.

The data preprocessing pipeline begins by parsing datetime strings into a structured format, enabling the extraction of fundamental temporal components including hour, day, month, year, and day of the week. A key innovation is the application of cyclical encoding to the hour and month variables, transforming them into sine and cosine components to preserve the continuous, periodic nature of these features and mitigate the arbitrary discontinuity inherent in their raw integer forms. Additional engineered features include a binary indicator for weekends. The pipeline handles both training and test sets identically, utilizing features such as season, weather conditions, and temperature without any explicit handling of missing data, suggesting the dataset is presumed complete.

The model architecture employs a single Random Forest Regressor, an ensemble method based on bagging decision trees. The hyperparameters were specified with a focus on regularization to prevent overfitting: 100 estimators, a maximum tree depth of 15, a minimum of 5 samples required to split an internal node, and a minimum of 5 samples required to be at a leaf node. The model operates natively as a regressor predicting continuous values. Notably, the approach is an ensemble only in the context of the Random Forest algorithm itself and does not implement a broader ensemble strategy combining multiple, diverse model types.

The validation strategy utilizes a standard holdout method, partitioning the training data via an 80-20 split with a fixed random state. The primary evaluation metric is the Root Mean Squared Logarithmic Error (RMSLE), chosen for its sensitivity to relative errors and appropriateness for predicting count data that can span several orders of magnitude. A critical post-processing step is applied to validation and test predictions, clamping all negative values to zero using `np.maximum` to align with the non-negative domain of the target variable, followed by rounding to the nearest integer for the final submission.

## 3. Appendix: Source Code

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_log_error
import warnings
warnings.filterwarnings('ignore')

# Load data
train_df = pd.read_csv('train.csv')
test_df = pd.read_csv('test.csv')

# Preprocessing function
def preprocess_data(df):
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Extract time-based features
    df['hour'] = df['datetime'].dt.hour
    df['day'] = df['datetime'].dt.day
    df['month'] = df['datetime'].dt.month
    df['year'] = df['datetime'].dt.year
    df['dayofweek'] = df['datetime'].dt.dayofweek
    
    # Cyclical encoding for hour and month
    df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24)
    df['month_sin'] = np.sin(2 * np.pi * df['month']/12)
    df['month_cos'] = np.cos(2 * np.pi * df['month']/12)
    
    # Weekend feature
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    
    return df

# Preprocess both datasets
train_processed = preprocess_data(train_df)
test_processed = preprocess_data(test_df)

# Define features and target
features = ['season', 'holiday', 'workingday', 'weather', 'temp', 'atemp', 
            'humidity', 'windspeed', 'hour', 'day', 'month', 'year', 
            'dayofweek', 'hour_sin', 'hour_cos', 'month_sin', 'month_cos', 'is_weekend']

X = train_processed[features]
y = train_processed['count']

X_test = test_processed[features]

# Split training data for validation
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Random Forest model
rf_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)

# Train model
rf_model.fit(X_train, y_train)

# Validation predictions
val_pred = rf_model.predict(X_val)
val_pred = np.maximum(0, val_pred)  # Ensure non-negative predictions

# Calculate RMSLE on validation set
val_rmsle = np.sqrt(mean_squared_log_error(y_val, val_pred))
print(f"Validation RMSLE: {val_rmsle:.4f}")

# Feature importance
importance_df = pd.DataFrame({
    'feature': features,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 10 Feature Importances:")
print(importance_df.head(10))

# Final predictions on test set
test_pred = rf_model.predict(X_test)
test_pred = np.maximum(0, test_pred)  # Ensure non-negative predictions

# Create submission file
submission_df = pd.DataFrame({
    'datetime': test_df['datetime'],
    'count': test_pred.round().astype(int)  # Round to integer counts
})

# Save submission file
submission_df.to_csv('submission_bike-sharing-demand_152d17.csv', index=False)
print(f"\nSubmission file saved successfully with {len(submission_df)} predictions")
```
---
*Report automatically generated by DSLighting Lead Researcher Tool.*
