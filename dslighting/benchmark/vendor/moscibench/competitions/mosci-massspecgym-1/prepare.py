from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

TASK_NAME = 'mosci-massspecgym-1'
FAMILY = 'massspecgym'
LOCAL_TASK_ID = 1
GLOBAL_TASK_ID = 32
ANSWER_VALUE = 'true'
LAYOUT = 'datasets_dir'
PUBLIC_TASK_SPEC = json.loads('[\n  {\n    "task_id": "mosci-massspecgym-1",\n    "family": "massspecgym",\n    "local_task_id": 1,\n    "global_task_id": 32,\n    "background": "Precursor m/z values are critical in mass spectrometry as they represent the mass-to-charge ratio of ions selected for fragmentation. Understanding the distribution of spectral counts across different precursor m/z values can provide insights into experimental biases, instrument performance, or the nature of analyzed samples in mass spectrometry studies.",\n    "hypothesis": "There are significant differences in the number of spectra corresponding to different precursor m/z values.",\n    "workflow": "1. Read the mass spectrometry data from the TSV file. 2. Calculate basic statistical information about precursor m/z values and their counts. 3. Perform a chi-square test to assess if the distribution of spectral counts across precursor m/z values is uniform. 4. Determine if there are significant differences based on the statistical test results.",\n    "scientific_domain": "cheminformatics",\n    "problem_type": "descriptive",\n    "task_type": "statistical tests",\n    "domain_knowledge": "In mass spectrometry, precursor m/z values indicate specific ions selected for analysis. A non-uniform distribution of spectral counts across these values may reflect ion selection biases, sample composition, or instrument sensitivity variations. The chi-square test is used to assess whether observed counts differ significantly from expected uniform counts.",\n    "modality": "tabular, mass spectra",\n    "answer_format": "There are significant differences in the number of spectra corresponding to different precursor m/z values. Determine if the statement is true or false. Format your answer as: answer: {true} or answer: {false}."\n  }\n]')
PUBLIC_DATA_DESCRIPTION = json.loads('{\n  "task_id": "mosci-massspecgym-1",\n  "family": "massspecgym",\n  "local_task_id": 1,\n  "global_task_id": 32,\n  "family_description_id": 4,\n  "domain": "Chemistry",\n  "modalities": "mass spectra, molecular structures",\n  "overall_description": "MassSpecGym is a benchmark dataset for the discovery and identification of molecules, focusing on mass spectrometry data. It includes various attributes related to molecular structures, mass spectral features, experimental conditions, and simulation challenges, which can be used to evaluate methods for molecular identification and mass spectrum analysis.",\n  "datasets": [\n    {\n      "name": "MassSpecGym.tsv",\n      "dataset_description": "A tabular dataset containing mass spectrometry-related information for a collection of molecules, including identifiers, mass spectral peaks, molecular formulas, structural representations, and experimental parameters.",\n      "columns": [\n        {\n          "name": "identifier",\n          "description": "A unique identifier for each entry in the MassSpecGym dataset, formatted as MassSpecGymID followed by a numerical value."\n        },\n        {\n          "name": "mzs",\n          "description": "A comma-separated list of mass-to-charge ratios (m/z) corresponding to the peaks in the mass spectrum."\n        },\n        {\n          "name": "intensities",\n          "description": "A comma-separated list of relative intensities of the corresponding m/z peaks in the mass spectrum, normalized such that the maximum intensity is 1.0."\n        },\n        {\n          "name": "smiles",\n          "description": "The Simplified Molecular-Input Line-Entry System string, which is a textual representation of the molecular structure."\n        },\n        {\n          "name": "inchikey",\n          "description": "A unique identifier for the molecular structure, generated from the InChI (International Chemical Identifier) to enable easy comparison of molecules."\n        },\n        {\n          "name": "formula",\n          "description": "The molecular formula of the compound, representing the types and numbers of atoms present in the molecule."\n        },\n        {\n          "name": "precursor_formula",\n          "description": "The molecular formula of the precursor ion, which is the ionized form of the molecule used in the mass spectrometry experiment."\n        },\n        {\n          "name": "parent_mass",\n          "description": "The mass of the neutral parent molecule, calculated based on its molecular formula."\n        },\n        {\n          "name": "precursor_mz",\n          "description": "The mass-to-charge ratio of the precursor ion selected for fragmentation in the mass spectrometry experiment."\n        },\n        {\n          "name": "adduct",\n          "description": "The type of adduct formed with the molecule during ionization, indicating the ion form (e.g., [M+H]+ represents a protonated molecule)."\n        },\n        {\n          "name": "instrument_type",\n          "description": "The type of mass spectrometry instrument used to acquire the mass spectrum (e.g., Orbitrap)."\n        },\n        {\n          "name": "collision_energy",\n          "description": "The collision energy applied during the fragmentation process, given in appropriate units (e.g., 30.0)."\n        }\n      ]\n    }\n  ]\n}')
PRIVATE_TASK_METADATA = json.loads('{\n  "task_id": "mosci-massspecgym-1",\n  "family": "massspecgym",\n  "local_task_id": 1,\n  "global_task_id": 32,\n  "judge_type": "=",\n  "evaluation": true,\n  "gold_hypothesis": "There are significant differences in the number of spectra corresponding to different precursor m/z values.",\n  "raw_task": {\n    "id": 1,\n    "background": "Precursor m/z values are critical in mass spectrometry as they represent the mass-to-charge ratio of ions selected for fragmentation. Understanding the distribution of spectral counts across different precursor m/z values can provide insights into experimental biases, instrument performance, or the nature of analyzed samples in mass spectrometry studies.",\n    "hypothesis": "There are significant differences in the number of spectra corresponding to different precursor m/z values.",\n    "workflow": "1. Read the mass spectrometry data from the TSV file. 2. Calculate basic statistical information about precursor m/z values and their counts. 3. Perform a chi-square test to assess if the distribution of spectral counts across precursor m/z values is uniform. 4. Determine if there are significant differences based on the statistical test results.",\n    "gold_hypothesis": "There are significant differences in the number of spectra corresponding to different precursor m/z values.",\n    "scientific_domain": "cheminformatics",\n    "problem_type": "descriptive",\n    "task_type": "statistical tests",\n    "domain_knowledge": "In mass spectrometry, precursor m/z values indicate specific ions selected for analysis. A non-uniform distribution of spectral counts across these values may reflect ion selection biases, sample composition, or instrument sensitivity variations. The chi-square test is used to assess whether observed counts differ significantly from expected uniform counts.",\n    "modality": "tabular, mass spectra",\n    "answer_format": "There are significant differences in the number of spectra corresponding to different precursor m/z values. Determine if the statement is true or false. Format your answer as: answer: {true} or answer: {false}.",\n    "evaluation": true,\n    "judge_type": "="\n  },\n  "family_data_description": {\n    "id": 4,\n    "domain": "Chemistry",\n    "overall_description": "MassSpecGym is a benchmark dataset for the discovery and identification of molecules, focusing on mass spectrometry data. It includes various attributes related to molecular structures, mass spectral features, experimental conditions, and simulation challenges, which can be used to evaluate methods for molecular identification and mass spectrum analysis.",\n    "modalities": "mass spectra, molecular structures",\n    "datasets": [\n      {\n        "name": "MassSpecGym.tsv",\n        "dataset_description": "A tabular dataset containing mass spectrometry-related information for a collection of molecules, including identifiers, mass spectral peaks, molecular formulas, structural representations, and experimental parameters.",\n        "columns": [\n          {\n            "name": "identifier",\n            "description": "A unique identifier for each entry in the MassSpecGym dataset, formatted as MassSpecGymID followed by a numerical value."\n          },\n          {\n            "name": "mzs",\n            "description": "A comma-separated list of mass-to-charge ratios (m/z) corresponding to the peaks in the mass spectrum."\n          },\n          {\n            "name": "intensities",\n            "description": "A comma-separated list of relative intensities of the corresponding m/z peaks in the mass spectrum, normalized such that the maximum intensity is 1.0."\n          },\n          {\n            "name": "smiles",\n            "description": "The Simplified Molecular-Input Line-Entry System string, which is a textual representation of the molecular structure."\n          },\n          {\n            "name": "inchikey",\n            "description": "A unique identifier for the molecular structure, generated from the InChI (International Chemical Identifier) to enable easy comparison of molecules."\n          },\n          {\n            "name": "formula",\n            "description": "The molecular formula of the compound, representing the types and numbers of atoms present in the molecule."\n          },\n          {\n            "name": "precursor_formula",\n            "description": "The molecular formula of the precursor ion, which is the ionized form of the molecule used in the mass spectrometry experiment."\n          },\n          {\n            "name": "parent_mass",\n            "description": "The mass of the neutral parent molecule, calculated based on its molecular formula."\n          },\n          {\n            "name": "precursor_mz",\n            "description": "The mass-to-charge ratio of the precursor ion selected for fragmentation in the mass spectrometry experiment."\n          },\n          {\n            "name": "adduct",\n            "description": "The type of adduct formed with the molecule during ionization, indicating the ion form (e.g., [M+H]+ represents a protonated molecule)."\n          },\n          {\n            "name": "instrument_type",\n            "description": "The type of mass spectrometry instrument used to acquire the mass spectrum (e.g., Orbitrap)."\n          },\n          {\n            "name": "collision_energy",\n            "description": "The collision energy applied during the fragmentation process, given in appropriate units (e.g., 30.0)."\n          }\n        ]\n      }\n    ]\n  }\n}')


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "answer"])
        writer.writeheader()
        writer.writerows(rows)


def _copy_payload(raw: Path, public: Path) -> None:
    datasets_dir = raw / "datasets"
    if not datasets_dir.exists():
        return
    if LAYOUT in {"datasets_dir", "both"}:
        dst = public / "datasets"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(datasets_dir, dst)
    if LAYOUT in {"flatten", "both"}:
        for item in datasets_dir.iterdir():
            dst = public / item.name
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    _copy_payload(raw, public)
    (public / "discovery_tasks.json").write_text(
        json.dumps(PUBLIC_TASK_SPEC, ensure_ascii=False, indent=2) + "\n"
    )
    (public / "data_description.json").write_text(
        json.dumps(PUBLIC_DATA_DESCRIPTION, ensure_ascii=False, indent=2) + "\n"
    )
    (private / "task_metadata.json").write_text(
        json.dumps(PRIVATE_TASK_METADATA, ensure_ascii=False, indent=2) + "\n"
    )
    _write_csv(
        private / "answer.csv",
        [{"id": str(GLOBAL_TASK_ID), "answer": f"@answer[{ANSWER_VALUE}]"}],
    )
    _write_csv(
        public / "sample_submission.csv",
        [{"id": str(GLOBAL_TASK_ID), "answer": "@answer[your_answer_here]"}],
    )
