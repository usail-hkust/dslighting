# Cheminformatics - Predictive

## Task Metadata

- Family: massspecgym
- Local Task ID: 12
- Problem Type: Predictive
- Modality: tabular, mass spectra

## Background

Molecular weight (MW) is a core property for molecular identification in mass spectrometry (MS), with a 10 ppm error threshold being a strict benchmark for reliable annotation (e.g., distinguishing isomers with subtle MW differences). MS/MS spectral peak intensity distribution reflects fragment ion abundance—driven by cleavage probability and fragment stability—which may encode indirect MW-related information. Evaluating whether this distribution can predict MW within 10 ppm is critical for validating its utility as a supplementary MW validation tool; failure to meet this threshold would indicate the distribution lacks sufficient MW-related signals for practical use.

## Task

Predicting molecular weight based on MS/MS spectral peak intensity distribution may achieve an error within 10 ppm (ppm_error = abs(predicted - actual) / actual * 1e6).

## Raw Answer Target

Molecular weight can be predicted based on the peak intensity distribution of MS/MS spectra, and the prediction accuracy can meet the requirement of an error within 10 ppm. Determine if the statement is true or false. Format your answer as: answer: {true} or answer: {false}.

## Domain Knowledge

Peak intensity distribution in MS/MS spectra is driven by fragment stability and cleavage efficiency—properties weakly correlated with molecular weights (e.g., similar MW molecules can have divergent fragment intensity patterns). PPM error normalizes MW prediction error to account for MW magnitude, making it the standard metric for MS-based MW accuracy. A 10 ppm threshold is required for reliable molecular matching (e.g., in metabolomics databases). Low R² and extremely high mean/median ppm error indicate the intensity distribution lacks sufficient MW-related signals.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `43`.
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
