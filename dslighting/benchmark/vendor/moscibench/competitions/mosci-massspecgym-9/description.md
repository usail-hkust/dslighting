# Cheminformatics - Causal Inference

## Task Metadata

- Family: massspecgym
- Local Task ID: 9
- Problem Type: Causal Inference
- Modality: tabular, mass spectra

## Background

Orbitrap and QTOF are two common high-resolution mass spectrometry (HRMS) technologies, each with distinct ion detection mechanisms: Orbitrap uses electrostatic trapping for high mass accuracy, while QTOF relies on time-of-flight measurement. These structural differences can theoretically introduce systematic biases in detected fragment ion intensities, even for the same molecule. Investigating whether instrument type directly causes such intensity biases—independent of molecular differences—is critical for MS/MS data integration and cross-lab comparison; if biases exist, normalization methods can be developed to standardize data across instruments.

## Task

Differences in instrument type (Orbitrap vs. QTOF) directly cause systematic biases in spectral peak intensities, rather than differences between molecules themselves.

## Raw Answer Target

Differences in instrument type (Orbitrap vs. QTOF) directly cause systematic biases in spectral peak intensities, rather than differences between molecules themselves. Determine if the statement is true or false. Format your answer as: answer: {true} or answer: {false}.

## Domain Knowledge

Normalizing spectral intensities (to total intensity = 1) eliminates variations from absolute signal strength, focusing on relative peak intensity differences. Using molecules measured on both instruments controls for molecular structure as a confounding variable, isolating instrument effects. A one-sample t-test against a ratio of 1 assesses if intensity differences are statistically significant (p<0.05 = unlikely due to randomness). Systematic bias refers to consistent, non-random intensity differences across peaks/molecules, which arises from instrument-specific detection physics (e.g., trapping efficiency in Orbitrap vs. flight path in QTOF).

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `40`.
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
