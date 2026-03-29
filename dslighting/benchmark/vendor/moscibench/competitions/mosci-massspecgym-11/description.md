# Cheminformatics - Predictive

## Task Metadata

- Family: massspecgym
- Local Task ID: 11
- Problem Type: Predictive
- Modality: tabular, molecular structures, mass spectra

## Background

The number of peaks in an MS/MS spectrum is jointly determined by molecular structure (e.g., bond strength, cleavable bond count) and collision energy (driving bond cleavage—higher energy typically induces more fragmentation). When using a Random Forest model to predict peak count based on these two factors, the accuracy within ±2 peak error is a critical practical metric: it directly reflects how often the model’s predictions are close enough to the actual peak count to support real-world applications (e.g., validating spectral data quality, guiding collision energy selection). This metric complements traditional regression metrics (MAE, RMSE) by focusing on actionable prediction precision.

## Task

A Random Forest model, trained on collision energy and molecular structural features, will have a quantifiable accuracy within ±2 peak error when predicting the number of peaks in MS/MS spectra.

## Raw Answer Target

Fill in the sentence: When using a Random Forest model to predict MS/MS spectral peak count based on collision energy and molecular structural features, the model achieves an accuracy of {accuracy_in_percentage}% within the ±2 peak error range.

## Domain Knowledge

Molecular structural features capture properties that influence fragmentation (e.g., more cleavable bonds = higher potential peak count), while collision energy controls fragmentation extent (non-linear relationship—diminishing returns at high energy). RobustScaler normalizes features without being skewed by outliers (critical for variable collision energy and peak count data). Random Forest Regressors excel at modeling non-linear feature-peak count relationships but may have limited precision. The ±2 error accuracy metric is practical for MS/MS applications: a low value indicates the model’s predictions are rarely within a narrow range of the actual peak count, likely due to complex fragmentation dynamics (e.g., variable fragment ion stability, instrument noise) not fully captured by structural and energy features.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `42`.
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
