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

Save columns `file_name` and `image_base64`. Encode the output PNG as base64 (UTF-8 string) and place it in the row for that filename.

## Evaluation

The grader decodes the submitted image, compares it against the reference visualization, and accepts the submission when the similarity score meets or exceeds 60.
