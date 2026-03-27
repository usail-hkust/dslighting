# ScienceBench Task 73

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Data Visualization
- Source: ZitongLu1996/EEG2EEG
- Output Type: Image

## Task

Visualize the original and generated EEG signal of Sub-03 using a line plot. Images and channels corresponding to each timepoint should be averaged before plotting. Save the line plot to "output file".

## Dataset

[START Dataset Preview: thingseeg2]
|-- train/sub01.npy
|-- train/sub03.npy
|-- test/sub01.npy
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
