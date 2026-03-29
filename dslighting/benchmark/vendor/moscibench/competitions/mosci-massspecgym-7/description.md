# Cheminformatics - Causal Inference

## Task Metadata

- Family: massspecgym
- Local Task ID: 7
- Problem Type: Causal Inference
- Modality: tabular, molecular structures, mass spectra

## Background

Specific chemical bonds (e.g., C=O double bonds, C-O single bonds) have distinct bond dissociation energies, which dictate their propensity to break during MS/MS fragmentation. When a bond breaks, it generates characteristic fragment ions with unique mass-to-charge (m/z) ratios. Investigating whether the presence of these bonds correlates with the occurrence of specific fragment peaks is critical for MS/MS spectral interpretation—if such associations exist, they can serve as 'bond-specific markers' to accelerate molecular structure elucidation and improve compound annotation accuracy.

## Task

The presence of specific chemical bonds (e.g., 'C=O double bond', 'C-O single bond', 'C-N single bond') in a molecule is significantly associated with the occurrence of specific fragment peaks in its MS/MS spectrum.

## Raw Answer Target

The presence of three specific chemical bonds ('C=O double bond', 'C-O single bond', 'C-N single bond') in a molecule is significantly associated with the occurrence of specific fragment peaks in its MS/MS spectrum. Determine if the statement is true or false. Format your answer as: answer: {true} or answer: {false}.

## Domain Knowledge

SMARTS patterns are standardized representations of molecular substructures, enabling reliable detection of specific chemical bonds (e.g., C=O double bonds) via substructure matching. Chi-square tests assess the statistical association between two categorical variables (bond presence/absence and peak occurrence/absence). Bonferroni correction adjusts p-values to reduce false positives when testing multiple m/z peaks. Distinct bond dissociation energies lead to bond-specific fragmentation, resulting in characteristic fragment ions whose occurrence correlates with the presence of the parent bond.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `38`.
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
