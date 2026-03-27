# ScienceBench Task 45

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: mad-lab-fau/BioPsyKit
- Output Type: Tabular

## Task

Given the questionnaire data, compute perceived stress scale (PSS) score.

## Dataset

[START Dataset Preview: biopsykit_questionnaire_data]
|-- questionnaire_data.pkl
[END Dataset Preview]

## Submission Format

Save a CSV file with the columns `subject` and computed scores matching the reference structure (`subject`, `PSS_total`, ...). Ensure the header and row order align with the template.

## Evaluation

The grader checks that every subject row exactly matches the reference questionnaire scores. Any mismatch fails the evaluation.
