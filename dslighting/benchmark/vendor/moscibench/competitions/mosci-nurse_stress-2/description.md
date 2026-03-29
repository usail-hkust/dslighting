# Health Psychology - Descriptive

## Task Metadata

- Family: nurse_stress
- Local Task ID: 2
- Problem Type: Descriptive
- Modality: timeseries, tabular

## Background

Skin temperature is regulated by the autonomic nervous system, which is known to respond to stress. Investigating whether skin temperature differs significantly between no-stress and high-stress periods can help validate its potential as an objective physiological marker for stress assessment in clinical or occupational settings.

## Task

There is a statistically significant difference in skin temperature between no-stress (stress level = 0) and high-stress (stress level = 2) periods among nurses.

## Raw Answer Target

There is a statistically significant difference in skin temperature between no-stress and high-stress periods among nurses. Determine if the significance statement is true or false. Format your response as: answer: {true} or answer: {false}.

## Domain Knowledge

Stress triggers autonomic nervous system responses, including vasoconstriction or vasodilation, which can alter skin temperature. Parametric tests (like t-tests) assume normal data distribution, while nonparametric tests (like Wilcoxon) are robust to violations of normality, making them suitable for physiological data with potential non-normal characteristics.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `48`.
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
**Modalities:** timeseries, tabular

This dataset is a multimodal sensor dataset for continuous stress detection of nurses, collected in a natural hospital working environment during the COVID-19 pandemic. It includes physiological signal data (such as electrodermal activity, heart rate, skin temperature, etc.) from 15 female nurses during their work and corresponding survey feedback on stress events. It aims to provide data support for the development of early detection algorithms for work-related stress in nurses, so as to deeply understand and improve nurses' emotional health in natural environments.

### Files

#### `subject_5C_combined.csv`
This file contains combined physiological signal data of the nurse with ID 5C, collected by the Empatica E4 wristband device. It covers time-series information of multiple physiological indicators during her work sessions, which can be used to analyze the correlation between physiological changes and stress status of this nurse during work. The rest of other 14 files follow the same format (file name: subject_{subject_ID}_combined.csv, same columns), each storing the signal data of a nurse with a different ID (6B, 6D, 7A, 7E, 8B, 15, 83, 94, BG, CE, DF, E4, EG, F5).

| Column | Description |
|---|---|
| `session` | Indicates the session identifier for data collection, composed of the nurse's ID and starting timestamp in UTC, used to distinguish different collection periods, for instance 5C_1586886626, indicating that data collection starts at 1586886626. |
| `real_time` | The actual time when the corresponding data point was recorded, presented in timestamp format with the unit of seconds, for instance 1586886636.0. Data points are recorded in 4Hz. |
| `eda` | The measurement value of Electrodermal Activity, with the unit of microsiemens (μS). It reflects changes in skin conductance level and is an important physiological indicator for stress measurement. |
| `hr` | Heart Rate, with the unit of beats per minute (bpm). It is an indicator derived from Blood Volume Pulse (BVP) and is used to represent the number of heartbeats per minute. |
| `temp` | Skin Temperature, with the unit of degrees Celsius (℃). It records the external temperature of the skin, and its changes may reflect stress status. |
| `bvp` | Blood Volume Pulse, with no unit. It refers to the volume of blood passing through the wrist tissues and can be used to measure heart rate. |

#### `survey_results.csv`
This csv file contains survey results and annotated stress levels of all 15 participating nurses. These survey data are linked to physiological signal data through the nurse's ID and date-time fields, which can be used to verify stress detection results and analyze the causes of detected stress events.

| Column | Description |
|---|---|
| `ID` | The anonymous identifier of the nurse, used to distinguish different nurse participants. ID used in this dataset: 5C, 6B, 6D, 7A, 7E, 8B, 15, 83, 94, BG, CE, DF, E4, EG, F5. |
| `Start time` | The start time of the detected stress event (already converted to UTC), for instance 2020-04-14 22:31:00. |
| `End time` | The end time of the detected stress event (already converted to UTC), for instance 2020-04-14 22:58:00. |
| `Duration` | The duration of the detected stress event, for instance 00:27:00. |
| `Date` | The specific date when the stress event was detected, for instance 2020-04-14. |
| `Stress level` | The stress level reported by the nurse. 0 for no stress, 1 for medium stress, 2 for high stress. |
| `COVID related` | Indicates whether the stress event is related to COVID, 0 for no, 1 for yes. |
| `Treating a COVID patient` | Indicates whether the stress event is caused by treating COVID patients, 0 for no, 1 for yes. |
| `Patient in crisis` | Indicates whether the stress event is caused by the patient being in a crisis state, 0 for no, 1 for yes. |
| `Patients or their family` | Indicates whether the stress event is caused by stress related to interaction with patients or their families, 0 for no, 1 for yes. |
| `Doctors or colleagues` | Indicates whether the stress event is caused by stress related to interaction with doctors or colleagues, 0 for no, 1 for yes. |
| `Ancilliary services` | Indicates whether the stress event is caused by stress related to administration, laboratory, pharmacy, radiology, or other ancillary services, 0 for no, 1 for yes. |
| `Increased workload` | Indicates whether the stress event is caused by increased workload, 0 for no, 1 for yes. |
| `Technology related stress` | Indicates whether the stress event is caused by technology-related stress, 0 for no, 1 for yes. |
| `Lack of supplies` | Indicates whether the stress event is caused by lack of supplies, 0 for no, 1 for yes. |
| `Documentation` | Indicates whether the stress event is caused by stress related to documentation work, 0 for no, 1 for yes. |
| `Competency related stress` | Indicates whether the stress event is caused by competency-related stress, 0 for no, 1 for yes. |
| `Safety` | Indicates whether the stress event is caused by stress related to safety (physical or physiological threats), 0 for no, 1 for yes. |
| `Work environment` | Indicates whether the stress event is caused by stress related to the work environment (physical or others: work processes or procedures), 0 for no, 1 for yes. |
