# Cheminformatics - Descriptive

## Task Metadata

- Family: massspecgym
- Local Task ID: 3
- Problem Type: Descriptive
- Modality: tabular, mass spectra

## Background

Collision energy is a key parameter in MS/MS experiments that directly influences molecular fragmentation, and spectral peak count serves as a proxy for fragmentation extent. Comparing peak counts across different mass spectrometry instruments (e.g., Orbitrap and QTOF) under the same collision energy intervals is critical for understanding instrument-specific performance in capturing fragmentation information, optimizing MS/MS conditions, and improving molecular identification accuracy.

## Task

Orbitrap instruments have a generally higher number of spectral peaks than QTOF instruments across various collision energy intervals.

## Raw Answer Target

Fill in the sentence: Across all applicable collision energy intervals, {choose from Orbitrap/QTOF} instruments consistently exhibit a higher average number of spectral peaks.

## Domain Knowledge

Different mass spectrometry instruments (Orbitrap vs. QTOF) vary in detection sensitivity, mass resolution, and ion transmission efficiency—factors that affect the number of detectable spectral peaks. Orbitrap instruments typically offer higher mass resolution and sensitivity, which may enable capture of more fragmentation ions (reflected in higher peak counts) compared to QTOF instruments under the same collision energy conditions. Comparing peak counts across instruments per collision energy interval helps quantify these performance differences.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `34`.
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
