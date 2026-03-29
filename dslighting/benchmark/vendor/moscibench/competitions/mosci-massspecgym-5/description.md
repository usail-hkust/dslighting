# Cheminformatics - Correlational

## Task Metadata

- Family: massspecgym
- Local Task ID: 5
- Problem Type: Correlational
- Modality: tabular, molecular structures, mass spectra

## Background

Functional groups (e.g., hydroxyl, carbonyl, carboxyl, amino) are distinct atomic arrangements in molecules that drive characteristic chemical reactions—including fragmentation behavior in MS/MS experiments. Specific functional groups may preferentially break into fragments with unique mass-to-charge (m/z) ratios, potentially linking their presence/absence to the frequency of specific m/z peaks in spectra. Investigating this correlation is critical for improving functional group annotation in mass spectrometry, enhancing molecular structure elucidation workflows, and validating fragment-ion associations with functional group characteristics.

## Task

The presence or absence of specific functional groups (hydroxyl, carbonyl, carboxyl, amino) in a molecule is correlated with the occurrence frequency of specific m/z peaks in its MS/MS spectrum.

## Raw Answer Target

The presence or absence of specific functional groups (hydroxyl, carbonyl, carboxyl, amino) in a molecule is correlated with the occurrence frequency of specific m/z peaks in its MS/MS spectrum. Determine if the statement is true or false. Format your answer as: answer: {true} or answer: {false}.

## Domain Knowledge

SMARTS patterns are standardized representations of molecular substructures, enabling reliable functional group identification via substructure matching. Chi-square tests assess associations between categorical variables (functional group presence/absence and peak occurrence/absence). Multiple-testing correction (e.g., Bonferroni) adjusts p-values to mitigate false positives when testing multiple m/z peaks. Functional groups drive specific fragmentation pathways, leading to unique fragment ions (specific m/z peaks) whose frequencies correlate with group presence.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `36`.
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
