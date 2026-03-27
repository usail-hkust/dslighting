# ScienceBench Task 44

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: mad-lab-fau/BioPsyKit
- Output Type: JSON

## Task

Analyze the inertial measurement unit (IMU) data collected during sleep and compute sleep endpoints. Load the given data and compute the following sleep endpoints: time of falling asleep, time of awakening, and total duration spent sleeping. The three values should be saved in a JSON file "output file", and the keys for them are "sleep_onset", "wake_onset", and "total_sleep_duration", respectively.

## Dataset

[START Dataset Preview: sleep_imu_data]
|-- sleep_data.pkl
[END Dataset Preview]

## Submission Format

Save a JSON file containing the keys `sleep_onset`, `wake_onset`, and `total_sleep_duration`. Use ISO-formatted timestamps for onset values and seconds for the total duration.

## Evaluation

The grader compares each entry against the reference values (string equality for timestamps and numerical closeness for durations). All three keys must match to pass.
