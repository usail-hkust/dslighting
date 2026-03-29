# Cheminformatics - Pattern Discovery

## Task Metadata

- Family: massspecgym
- Local Task ID: 15
- Problem Type: Pattern Discovery
- Modality: tabular, mass spectra

## Background

Collision energy (CE) directly influences molecular bond cleavage in MS/MS, with stronger bonds requiring higher CE to generate fragments. 'Enhanced fragments' are those whose intensity increases with higher CE, corresponding to bonds with high dissociation energy. Quantifying the proportion of such fragments is critical for understanding energy-dependent fragmentation dynamics—this metric reveals how many fragments require specific energy thresholds, guiding optimal CE selection for detecting target fragments and validating the relationship between bond strength and energy requirements.

## Task

When classifying molecular fragments by their energy response characteristics, 'enhanced fragments' (intensity increasing with collision energy) constitute a quantifiable proportion of all fragments, reflecting the prevalence of high-energy-requiring bonds in the dataset.

## Raw Answer Target

Fill in the sentence: When classifying molecular fragments by energy response characteristics, 'enhanced fragments' (intensity increasing with collision energy) account for {proportion_in_percentage}% of all fragments.

## Domain Knowledge

Normalizing spectral intensity allows comparison of relative fragment abundance across collision energies, isolating energy-dependent trends from absolute signal variation. Linear regression of intensity vs. CE identifies fragments with significant positive slopes, corresponding to bonds requiring higher energy for cleavage (e.g., C-C bonds in aromatic rings). The proportion quantifies how many fragments exhibit this behavior. This metric is key for interpreting how energy inputs shape fragmentation patterns and optimizing MS/MS conditions for target fragments.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `46`.
Put only the final answer value inside `@answer[...]`.
Do not submit the full sentence unless the answer itself is a full sentence.
The grader will strip common prefixes such as `answer:` automatically.

Examples:
- numeric: `@answer[7.4]`
- boolean: `@answer[true]`
- string: `@answer[Temperature]`
- structured text: `@answer[[(3, -78)]]`

## Dataset Description
**Domain:** Chemistry
**Modalities:** mass spectra, molecular structures

MassSpecGym is a benchmark dataset for the discovery and identification of molecules, focusing on mass spectrometry data. It includes various attributes related to molecular structures, mass spectral features, experimental conditions, and simulation challenges, which can be used to evaluate methods for molecular identification and mass spectrum analysis.

### Files

#### `MassSpecGym.tsv`
A tabular dataset containing mass spectrometry-related information for a collection of molecules, including identifiers, mass spectral peaks, molecular formulas, structural representations, and experimental parameters.

| Column | Description |
|---|---|
| `identifier` | A unique identifier for each entry in the MassSpecGym dataset, formatted as MassSpecGymID followed by a numerical value. |
| `mzs` | A comma-separated list of mass-to-charge ratios (m/z) corresponding to the peaks in the mass spectrum. |
| `intensities` | A comma-separated list of relative intensities of the corresponding m/z peaks in the mass spectrum, normalized such that the maximum intensity is 1.0. |
| `smiles` | The Simplified Molecular-Input Line-Entry System string, which is a textual representation of the molecular structure. |
| `inchikey` | A unique identifier for the molecular structure, generated from the InChI (International Chemical Identifier) to enable easy comparison of molecules. |
| `formula` | The molecular formula of the compound, representing the types and numbers of atoms present in the molecule. |
| `precursor_formula` | The molecular formula of the precursor ion, which is the ionized form of the molecule used in the mass spectrometry experiment. |
| `parent_mass` | The mass of the neutral parent molecule, calculated based on its molecular formula. |
| `precursor_mz` | The mass-to-charge ratio of the precursor ion selected for fragmentation in the mass spectrometry experiment. |
| `adduct` | The type of adduct formed with the molecule during ionization, indicating the ion form (e.g., [M+H]+ represents a protonated molecule). |
| `instrument_type` | The type of mass spectrometry instrument used to acquire the mass spectrum (e.g., Orbitrap). |
| `collision_energy` | The collision energy applied during the fragmentation process, given in appropriate units (e.g., 30.0). |
