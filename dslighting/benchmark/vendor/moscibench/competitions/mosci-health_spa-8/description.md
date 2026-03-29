# Biomedical Engineering - Causal Inference

## Task Metadata

- Family: health_spa
- Local Task ID: 8
- Problem Type: Causal Inference
- Modality: timeseries (multi sensors)

## Background

Sudden changes in environmental stimuli, such as light, can trigger responses in the autonomic nervous system. This study investigates whether a sudden, significant increase in light intensity causes a corresponding short-term acceleration in heart rate, a key physiological indicator.

## Task

A sudden increase in light intensity may trigger a short-term acceleration in heart rate.

## Raw Answer Target

A sudden increase in light intensity will trigger a short-term acceleration in heart rate. Determine if the causal inference statement is true or false. Format your answer as: answer: {true} or answer: {false}.

## Domain Knowledge

Sudden environmental changes (such as light intensity) can potentially affect physiological indicators like heart rate through autonomic nervous system responses. Paired t-tests are suitable for comparing related samples (before and after an event) to detect significant differences. Correlation analysis assesses the linear relationship between variable changes but does not imply causation.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `22`.
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
