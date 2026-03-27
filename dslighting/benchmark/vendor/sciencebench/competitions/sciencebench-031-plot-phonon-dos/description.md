# ScienceBench Task 31

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Computational Analysis, Data Visualization
- Source: materialsproject/pymatgen
- Output Type: Image

## Task

Use `vasprun.dfpt.phonon.xml.gz` to reconstruct the phonon density of states. Make sure the DOS axes are labeled, include legends for projected curves if present, and export the visualization to the output image path defined by the submission template.

## Dataset

[START Dataset Preview: materials_genomics]
|-- F_CHGCAR
|-- LiMoS2_F_CHGCAR
|-- LiMoS2_CHGCAR
|-- vasprun.dfpt.phonon.xml.gz
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
