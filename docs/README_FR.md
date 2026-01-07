<div align="center">

# DSLIGHTING Guide Français

Assistant personnalisé en mathématiques et sciences, axé sur un flux complet de data science.

[Démarrage rapide](#démarrage-rapide) · [Workflows](#workflows) · [Structure des données](#structure-des-données) · [Configuration](#configuration)

</div>

## Aperçu

DSLIGHTING fournit une entrée unique, des workflows extensibles et une structure de données standard,
couvrant la préparation, la modélisation, l’évaluation et la consolidation des résultats.

## Points forts

- Exécution bout-en-bout via une CLI unifiée
- Workflows AIDE / AutoMind / DSAgent / AFlow, etc.
- Journalisation automatique des exécutions et artefacts
- Enregistrement des tâches et préparation des données extensibles

## Workflows

- `aide` : boucle génération/exécution/revue
- `automind` : planification + mémoire + décomposition
- `dsagent` : plan/exécution structurés
- `data_interpreter` : exécution et débogage rapides
- `autokaggle` : workflow Kaggle SOP
- `aflow` : méta-optimisation de workflows
- `deepanalyze` : exécution orientée analyse

## Démarrage rapide

### 1. Préparer l’environnement

```bash
git clone <repository_url>
cd dslighting
python -m venv dsat
source dsat/bin/activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer les clés API

```bash
cp .env.example .env
```

### 4. Exemple d’exécution

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --data-dir data/competitions \
  --task-id bike-sharing-demand
```

## Structure des données

```
data/competitions/
  <competition-id>/
    config.yaml
    prepared/
      public/
      private/
```

ScienceBench suit la même structure.

## Configuration

`config.yaml` permet de définir :

- `competitions` : liste par défaut MLEBench
- `sciencebench_competitions` : liste par défaut ScienceBench
- `custom_model_pricing` : tarification LiteLLM
- `run` : paramètres de journalisation

---

[English](../README.md) · [中文](README_CN.md) · [日本語](README_JA.md)
