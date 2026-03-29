# Biomedical Engineering - Correlational

## Task Metadata

- Family: health_spa
- Local Task ID: 5
- Problem Type: Correlational
- Modality: timeseries (multi sensors)

## Background

Quantifying the correlation between environmental factors and physiological signals can help identify environmental modulators of health and well-being. This analysis seeks the strongest environmental correlates for heart rate and skin resistance.

## Task

Among various environmental variables, some will have stronger correlations with heart rate.

## Raw Answer Target

Please fill in the sentence: {hr_strongest_correlated_environment_variable_name} has the strongest correlation with heart rate.

## Domain Knowledge

The Pearson correlation coefficient (r) measures the strength and direction of a linear relationship between two continuous variables. The p-value determines the statistical significance of the correlation.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `19`.
Put only the final answer value inside `@answer[...]`.
Do not submit the full sentence unless the answer itself is a full sentence.
The grader will strip common prefixes such as `answer:` automatically.

Examples:
- numeric: `@answer[7.4]`
- boolean: `@answer[true]`
- string: `@answer[Temperature]`
- structured text: `@answer[[(3, -78)]]`

## Dataset Description
**Domain:** Medical Informatics
**Modalities:** multimodal timeseries

This dataset is a multimodal collection of physiological and environmental signals, designed to explore the relationships between indoor ambient conditions and individuals' physiological responses. It includes simultaneous and continuous recordings of electrodermal activity, cardiac activity, and various environmental parameters (such as light, temperature, humidity, pressure, air quality, and particulate matter) from human participants under controlled experimental scenarios. The dataset supports research on environmental risk classification for cardiac health and estimation of physiological indicators using ambient environment signals, facilitating advancements in context-aware health monitoring and proactive well-being interventions.

### Files

#### `subject_physiological_environmental_data.csv`
A multimodal timeseries dataset containing synchronized physiological measurements and environmental parameters from individual participants, capturing real-time variations under controlled indoor scenarios.

| Column | Description |
|---|---|
| `Skin Resistance` | A physiological parameter reflecting electrodermal activity, which indicates stress or arousal levels. Measured through the Grove Galvanic Skin Response (GSR) sensor affixed to participants' fingers. |
| `Light` | Ambient light intensity measured in lux using the VEML7700 sensor, capturing variations in indoor lighting conditions (range: 0 to ~120,000 lux). |
| `Nr.particles0.3` | Count of airborne particles with diameters exceeding 0.3 micrometers, measured by the PLANTOWER PMS5003 sensor, contributing to air quality assessment. |
| `Nr.particles0.5` | Count of airborne particles with diameters exceeding 0.5 micrometers, measured by the PLANTOWER PMS5003 sensor, reflecting fine particulate matter levels in the indoor environment. |
| `Nr.particles1.0` | Count of airborne particles with diameters exceeding 1.0 micrometer, measured by the PLANTOWER PMS5003 sensor, part of the air quality evaluation metrics. |
| `Temperature` | Indoor ambient temperature measured in degrees Celsius using the Bosch BME680 sensor, with a control accuracy of ±1 °C in the experimental chamber. |
| `Humidity` | Relative humidity in the indoor environment, measured as a percentage using the Bosch BME680 sensor, with a control accuracy of ±3% in the experimental chamber. |
| `Pressure` | Barometric pressure measured in hectopascals (hPa) using the Bosch BME680 sensor, capturing atmospheric pressure variations in the indoor environment. |
| `IAQ` | Indoor Air Quality index derived from volatile organic compound (VOC) detection by the Bosch BME680 sensor, reflecting overall air quality conditions. |
| `Sound` | Ambient sound levels measured in decibels (dBA) using the Bosch iNVH mobile application, capturing noise variations in the indoor environment. |
| `Heart Rate` | A vital cardiovascular health indicator, derived from raw electrocardiogram (ECG) data recorded by the Maxim Integrated MAX30001 evaluation kit, reflecting the number of heartbeats per minute. |
| `Subject` | Identifier for the participant in the study, representing individual participants from the cohort of 14 individuals with diverse demographic characteristics. |
| `Relative_Index` | An index variable potentially representing relative time or sequence within the experimental scenario, aiding in temporal alignment of measurements. |
