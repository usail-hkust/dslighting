# Cheminformatics - Pattern Discovery

## Task Metadata

- Family: massspecgym
- Local Task ID: 14
- Problem Type: Pattern Discovery
- Modality: tabular, molecular structures, mass spectra

## Background

Chemical classes are defined by shared structural features that produce conserved fragmentation patterns in MS/MS spectra, acting as 'fingerprints' for class identification. Known classes like alcohols, amines, carboxylic acids, aromatics, amides, ketones, esters have well-characterized patterns. In large datasets, unannotated molecules may belong to new, unknown classes with unique conserved fragmentation patterns. Detecting these patterns is critical for expanding chemical databases, identifying novel molecules, and understanding understudied chemical processes. Validating new classes requires confirming their unique patterns are distinct from known classes and consistent across multiple samples.

## Task

Beyond known chemical classes (alcohols, amines, carboxylic acids, aromatics, amides, ketones, esters), the dataset's mass spectra contain new chemical classes represented by unique conserved fragmentation patterns that do not correspond to any known class.

## Raw Answer Target

Beyond known chemical classes (alcohols, amines, carboxylic acids, aromatics, amides, ketones, esters), the dataset's mass spectra contain new chemical classes represented by unique conserved fragmentation patterns that do not correspond to any known class. Determine if the statement is true or false. Format your answer as: answer: {true} or answer: {false}.

## Domain Knowledge

Conserved fragmentation patterns (recurring m/z values in a cluster) indicate shared structural features, the basis of chemical class definition. Sparse feature matrices efficiently handle high-dimensional spectral data, focusing on significant peaks. DBSCAN clusters similar spectra without predefining cluster numbers, ideal for discovering unknown groups. A new class is validated if its conserved pattern is statistically distinct from known classes (via pattern matching) and consistently appears across multiple samples, ensuring it represents a genuine structural group rather than noise or artifacts. This approach leverages the link between fragmentation patterns and molecular structure to identify previously unrecognized chemical classes.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `45`.
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
