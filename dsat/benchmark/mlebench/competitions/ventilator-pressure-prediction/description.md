# Ventilator Pressure Prediction

## Description

Mechanical ventilation is a clinician-intensive procedure that was prominently on display during the early days of the COVID-19 pandemic. Current simulators are trained as an ensemble, where each model simulates a single lung setting. However, lungs form a continuous space, so a parametric approach must be explored.

In this competition, you'll simulate a ventilator connected to a sedated patient's lung. The best submissions will take lung attributes compliance and resistance into account. If successful, you'll help overcome the cost barrier of developing new methods for controlling mechanical ventilators.

## Evaluation

The competition is scored as the **mean absolute error (MAE)** between the predicted and actual pressures during the inspiratory phase of each breath. The expiratory phase is not scored.

$$\text{MAE} = \frac{1}{n}\sum_{i=1}^{n}|X_i - Y_i|$$

where $X$ is the vector of predicted pressure and $Y$ is the vector of actual pressures.

## Submission Format

For each id in the test set, you must predict a value for the pressure variable:

```
id,pressure
1,20
2,23
3,24
...
```

## Dataset Description

The ventilator data was produced using a modified open-source ventilator connected to an artificial bellows test lung via a respiratory circuit. Each time series represents an approximately 3-second breath.

## Columns

- `id`: globally-unique time step identifier
- `breath_id`: globally-unique breath identifier
- `R`: lung resistance (cmH2O/L/S)
- `C`: lung compliance (mL/cmH2O)
- `time_step`: actual time stamp
- `u_in`: inspiratory solenoid valve control (0-100)
- `u_out`: exploratory solenoid valve control (0 or 1)
- `pressure`: airway pressure (cmH2O) - target variable

## Files

- `train.csv`: Training set
- `test.csv`: Test set
- `sample_submission.csv`: Sample submission in correct format
