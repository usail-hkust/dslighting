# Cheminformatics - Correlational

## Task Metadata

- Family: massspecgym
- Local Task ID: 4
- Problem Type: Correlational
- Modality: tabular, mass spectra

## Background

Molecular weight reflects the total mass of a molecule, and larger molecules theoretically have more bonds available for fragmentation in MS/MS experiments—this may imply a potential relationship with spectral peak count (a measure of fragmentation extent). Investigating the strength of correlation between molecular weight and MS/MS peak count is essential for clarifying whether molecular weight contributes meaningfully to fragmentation extent, which in turn supports optimized molecular identification and MS method development by distinguishing major vs. minor influencing factors.

## Task

The correlation between a molecule's molecular weight and the number of peaks in its MS/MS spectrum is characterized by a specific strength (e.g., strong, moderate, weak, or negligible).

## Raw Answer Target

Fill in the sentence: The correlation between a molecule's molecular weight and MS/MS spectral peak count is {choose from extremely weak/weak/moderate/strong}.

## Domain Knowledge

Correlation strength is typically interpreted via coefficient magnitudes: Pearson/Spearman coefficients with absolute values <0.2 indicate negligible/extremely weak correlation, 0.2-0.4 indicate weak correlation, 0.4-0.6 indicate moderate correlation, and >0.6 indicate strong correlation. Statistical significance (p<0.05) confirms the correlation is not due to random chance, but does not equate to practical relevance. While larger molecules have more potential fragmentation sites, other factors (e.g., bond strength, chemical structure, collision energy) often dominate fragmentation—explaining why molecular weight’s correlation with MS/MS peak count is extremely weak.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `35`.
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
