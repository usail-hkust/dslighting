# Cheminformatics - Correlational

## Task Metadata

- Family: massspecgym
- Local Task ID: 6
- Problem Type: Correlational
- Modality: tabular, molecular structures, mass spectra

## Background

Morgan fingerprints encode molecular structural features (e.g., functional groups, substructures) into bit vectors, with their similarity reflecting structural resemblance between molecules. MS/MS spectral cosine similarity quantifies how closely fragmentation patterns (and thus fragment ion profiles) align between molecules. Investigating the specific correlation coefficients between these two similarities is critical for quantifying the link between molecular structure and fragmentation behavior—these coefficients directly reveal the strength and statistical reliability of the structural-spectral similarity relationship, which informs improvements in molecular annotation and structure prediction workflows in mass spectrometry.

## Task

The correlation coefficients between the Morgan fingerprint similarity of molecules and the cosine similarity of their MS/MS spectra can be quantified via Pearson correlation analysis, with the numerical value reflecting the strength of their association.

## Raw Answer Target

Fill in the sentence: The Pearson correlation coefficient between molecular Morgan fingerprint similarity and MS/MS spectral cosine similarity is {pearson_correlation_coefficient}.

## Domain Knowledge

Morgan fingerprints (e.g., ECFP4) capture structural features by hashing substructures around each atom, with similarity scores (0-1) indicating structural overlap. Spectral cosine similarity (0-1) measures the angle between intensity vectors of aligned m/z peaks, reflecting fragmentation pattern similarity. Pearson correlation quantifies linear positive relationships. Weak correlation arises because fragmentation is influenced by factors beyond structure (e.g., collision energy, instrument type), even as structure remains a foundational driver.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `37`.
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
