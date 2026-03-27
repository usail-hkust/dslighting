# ScienceBench Task 30

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Computational Analysis, Data Visualization
- Source: materialsproject/pymatgen
- Output Type: Image

## Task

Read the DFPT results in `vasprun.dfpt.phonon.xml.gz`, reconstruct the phonon dispersion, and render the band structure plot with an appropriate high-symmetry path. Keep the axes labeled and include a legend if multiple branches require clarification. Store the visualization in the output image file expected by the submission template.

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
