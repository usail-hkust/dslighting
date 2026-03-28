# ScienceBench Task 43

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis, Data Visualization
- Source: neuropsychology/NeuroKit
- Output Type: Image

## Task

Process the EOG signal to detect and visualise eye blinks. Clean the signal, detect peaks, build epochs around each blink, and plot the aligned traces together with the median blink pattern. Save the final figure as a PNG file.

## Dataset

[START Dataset Preview: biosignals]
|-- eog_100hz.csv
[END Dataset Preview]

## Submission Format

Save a single PNG file named `sample_submission.png`.

## Evaluation

The grader compares the submitted image against the reference visualization and accepts the submission when the similarity score meets or exceeds 60.
