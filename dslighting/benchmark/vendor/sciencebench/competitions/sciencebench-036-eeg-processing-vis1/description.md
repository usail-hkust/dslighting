# EEG Processing and Visualization

## Overview

This task focuses on processing electroencephalogram (EEG) data and visualizing EEG frequency band power.

## Task Description

Process the EEG data and plot the 20-point moving average of its EEG frequency band power. The output figure should be a line chart of the four functionally distinct frequency bands with respect to the timestamp.

## Dataset

The dataset contains EEG measurements from a Muse headband with the following features:
- `timestamps`: Unix timestamps in seconds
- `TP9`: EEG channel TP9 (left ear)
- `AF7`: EEG channel AF7 (left forehead)
- `AF8`: EEG channel AF8 (right forehead)
- `TP10`: EEG channel TP10 (right ear)
- `Right AUX`: Auxiliary channel

The data file is `eeg_muse_example.csv` located in the public data directory.



## Task Requirements

1. Load the EEG data from `eeg_muse_example.csv`
2. Calculate the frequency band power for each of the four frequency bands (Delta, Theta, Alpha, Beta)
3. Compute the 20-point moving average of each frequency band
4. Create a line chart showing all four frequency bands over time
5. Save the figure

## Tools and Libraries

You may use **BioPsyKit** for the analysis of biopsychological data. BioPsyKit is a Python package for processing and analyzing biosignals.

Reference: https://github.com/mad-lab-fau/BioPsyKit


## Evaluation

Your submission will be evaluated by comparing your generated figure with the gold standard figure using visual similarity metrics. The score must be >= 60 (out of 100) to pass.
