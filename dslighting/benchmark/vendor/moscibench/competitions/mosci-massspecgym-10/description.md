# Cheminformatics - Predictive

## Task Metadata

- Family: massspecgym
- Local Task ID: 10
- Problem Type: Predictive
- Modality: tabular, molecular structures, mass spectra

## Background

Chemical classes (lipid, carbohydrate, amino acid, alkaloid, other) have distinct structural features that drive unique MS/MS fragmentation behaviors—e.g., lipids fragment at long carbon chains, while carbohydrates cleave at glycosidic bonds. These class-specific patterns (encoded in MS/MS spectral features) can be learned by classifiers to predict molecular chemical classes. Quantifying the prediction accuracy for these five classes is critical for validating the utility of MS/MS spectra in high-throughput metabolomics/proteomics, where reliable class prediction streamlines molecular annotation and reduces computational complexity.

## Task

Based on MS/MS spectral features, the prediction accuracy of molecular chemical classes (lipid, carbohydrate, amino acid, alkaloid, other) can be quantified via classifiers, with the best-performing model achieving a measurable test set accuracy.

## Raw Answer Target

Fill in the sentence: Based on MS/MS spectral features, the best-performing model for predicting the five molecular chemical classes (lipid, carbohydrate, amino acid, alkaloid, other) achieves a test set accuracy of {test_set_accuracy}.

## Domain Knowledge

SMILES-based structural matching or pre-labeled data assigns molecules to the five chemical classes, ensuring class labels are ground-truth. MS/MS spectral features (peak m/z, normalized intensity) capture class-specific fragmentation—e.g., lipids produce characteristic fatty acid fragments, while amino acids generate immonium ions. Stratified sampling maintains class balance in training/test sets, preventing overfitting to large classes. Fast Random Forest outperforms K-Nearest Neighbors here due to its ability to handle non-linear feature relationships and reduce bias from imbalanced classes. Test set accuracy reflects overall predictive performance, while class-specific metrics highlight limitations.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `41`.
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
