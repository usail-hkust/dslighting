# Population Genomics - Predictive

## Task Metadata

- Family: pop_genetics
- Local Task ID: 8
- Problem Type: Predictive
- Modality: genotype matrix, tabular

## Background

Exploring the predictive ability of shared IBD segments (measured by IBS values) for two individuals’ same-population membership is important for population genetic studies, and the AUC (Area Under the ROC Curve) metric quantifies the model’s discriminative performance—making it critical to determine the specific AUC value when using shared IBD segment quantity for this prediction.

## Task

When using the number of shared IBD segments (measured by IBS values) to predict whether two individuals belong to the same population, a specific AUC value can be calculated to evaluate the model’s predictive performance.

## Raw Answer Target

Fill in the sentence: When using the number of shared IBD segments (measured by IBS values) to predict whether two individuals belong to the same population, the calculated AUC is {AUC_score}.

## Domain Knowledge

Identity By State (IBS) reflects the proportion of identical alleles between two individuals, which is closely related to the quantity of shared IBD segments. AUC (Area Under the ROC Curve) is a key metric for evaluating binary classification models: an AUC around 0.5 indicates no discriminative ability, 0.7-0.8 indicates acceptable performance, and >0.8 indicates good performance—making it ideal for quantifying how well shared IBD segment quantity predicts same-population membership.

## Submission Format

Use `sample_submission.csv` with columns `id,answer`.
Keep the `id` value as `69`.
Put only the final answer value inside `@answer[...]`.
Do not submit the full sentence unless the answer itself is a full sentence.
The grader will strip common prefixes such as `answer:` automatically.

Examples:
- numeric: `@answer[7.4]`
- boolean: `@answer[true]`
- string: `@answer[Temperature]`
- structured text: `@answer[[(3, -78)]]`

## Dataset Description
**Domain:** Bioinformatics
**Modalities:** genotype matrix, text, tabular

This dataset contains genotype data and related population information for studying the genetic landscape of modern France, including genotype data of samples from different regions in France and Naples, Italy (stored in PLINK bed, bim, and fam formats) as well as basic information of various French groups (such as geographical location, number of samples, number of filtered SNPs, etc.). These data can be used to analyze the internal genetic structure of the French group as well as relationships with surrounding populations.

### Files

#### `France_Group_Info.csv`
Contains basic information of different regional groups in France, describing the geographical location, number of samples, number of filtered SNPs, etc., of each group, providing basic group background information for genetic analysis.

| Column | Description |
|---|---|
| `Group` | Abbreviation of each regional group in France, representing different administrative regions (e.g., Bas-Rhin is abbreviated as BR), used to distinguish different sample groups. Groups in this dataset: BR, IeV, PdD, NO, PAR, BdR, HG. |
| `average_LAT` | Average latitude of the region where the samples of the group are located, reflecting the geographical latitude position of the samples |
| `average_LON` | Average longitude of the region where the samples of the group are located, reflecting the geographical longitude position of the samples |
| `num_samples` | Number of samples included in the group, reflecting the collection scale of samples in each region |
| `filtered_SNP_count` | Number of SNPs retained in the group after quality filtering, reflecting the number of effective genetic markers available for genetic analysis |

#### `France_Group.bed`
Binary file encoding the genotype matrix of samples from various regions in France. Each row corresponds to the genotypic data of an individual, and each column to a SNP. Genotypes are coded in binary to represent allele combinations (e.g., homozygous reference, heterozygous, homozygous alternate).

#### `France_Group.bim`
This text file contains SNP annotations for each variant site in the .bed file. Each row represents a single SNP, providing genomic position and allele identity. This file is essential for mapping genotypes to specific chromosomal positions.

| Column | Description |
|---|---|
| `chromosome` | Chromosome number where the SNP is located, indicating the chromosomal position of the SNP in the genome |
| `snp_id` | Unique identifier of the SNP (such as rs number), used to identify specific SNP loci |
| `genetic_distance` | Genetic distance between SNPs, usually in centimorgans (cM), reflecting the relative positional relationship of SNPs on the genetic map |
| `bp_position` | Physical position of the SNP on the chromosome, in base pairs (bp), accurately indicating the genomic coordinate of the SNP |
| `allele1` | First allele of the SNP, representing one possible base type at the locus (often ancestral or major allele) |
| `allele2` | Second allele of the SNP, representing another possible base type at the locus (often derived or minor allele) |

#### `France_Group.fam`
PLINK fam format file containing pedigree information and phenotypic data of French samples, used to identify sample individuals and related attributes.

| Column | Description |
|---|---|
| `family_id` | Identifier of the population to which the sample belongs, used to distinguish different populations |
| `individual_id` | Unique identifier of the sample individual, used to identify each specific sample |
| `paternal_id` | Identifier of the father of the sample individual, 0 indicates that the father's information is unknown |
| `maternal_id` | Identifier of the mother of the sample individual, 0 indicates that the mother's information is unknown |
| `sex` | Sex of the sample individual, 1 indicates male, 2 indicates female |
| `phenotype` | Phenotypic data of the sample individual, -9 usually indicates that the phenotypic data is missing or unspecified |

#### `Naples_Group.bed`
Genotype matrix data of samples from Naples, Italy stored in PLINK bed format, containing genotyping information of Naples samples, used for comparative analysis with French samples to explore genetic relationships. Each row corresponds to the genotypic data of an individual, and each column to a SNP. Genotypes are coded in binary to represent allele combinations (e.g., homozygous reference, heterozygous, homozygous alternate).

#### `Naples_Group.bim`
This text file contains SNP annotations for each variant site in the .bed file. Each row represents a single SNP, providing genomic position and allele identity. This file is essential for mapping genotypes to specific chromosomal positions.

| Column | Description |
|---|---|
| `chromosome` | Chromosome number where the SNP is located, indicating the chromosomal position of the SNP in the genome |
| `snp_id` | Unique identifier of the SNP (such as rs number), used to identify specific SNP loci |
| `genetic_distance` | Genetic distance between SNPs, usually in centimorgans (cM), reflecting the relative positional relationship of SNPs on the genetic map |
| `bp_position` | Physical position of the SNP on the chromosome, in base pairs (bp), accurately indicating the genomic coordinate of the SNP |
| `allele1` | First allele of the SNP, representing one possible base type at the locus (often ancestral or major allele) |
| `allele2` | Second allele of the SNP, representing another possible base type at the locus (often derived or minor allele) |

#### `Naples_Group.fam`
PLINK fam format file containing pedigree information and phenotypic data of Naples samples, used to identify sample individuals and related attributes.

| Column | Description |
|---|---|
| `family_id` | Identifier of the population to which the sample belongs, used to distinguish different populations |
| `individual_id` | Unique identifier of the sample individual, used to identify each specific sample |
| `paternal_id` | Identifier of the father of the sample individual, 0 indicates that the father's information is unknown |
| `maternal_id` | Identifier of the mother of the sample individual, 0 indicates that the mother's information is unknown |
| `sex` | Sex of the sample individual, 1 indicates male, 2 indicates female |
| `phenotype` | Phenotypic data of the sample individual, -9 usually indicates that the phenotypic data is missing or unspecified |
