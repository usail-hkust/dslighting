<div align="center">

<img src="../assets/dslighting.png" alt="DSLIGHTING Logo" width="180" style="border-radius: 15px;">

# DSLIGHTING : Assistant de workflow Data Science full-stack

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-2.7.8-blue?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/dslighting/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dslighting?style=flat-square&logo=pypi)](https://pypi.org/project/dslighting/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](../LICENSE)

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/🚀-Quick_Start-green?style=for-the-badge" alt="Quick Start"></a>
  &nbsp;&nbsp;
  <a href="#core-features"><img src="https://img.shields.io/badge/⚡-Features-blue?style=for-the-badge" alt="Core Features"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/"><img src="https://img.shields.io/badge/📚-Docs-orange?style=for-the-badge" alt="Documentation"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/guide/getting-started.html"><img src="https://img.shields.io/badge/📖-User_Guide-purple?style=for-the-badge" alt="User Guide"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/stargazers"><img src="https://img.shields.io/github/stars/usail-hkust/dslighting?style=for-the-badge" alt="Stars"></a>
  &nbsp;&nbsp;
  <img src="https://komarev.com/ghpvc/?username=usail-hkust&repo=dslighting&style=for-the-badge" alt="Profile views">
</p>

[🇨🇳 中文](../README.md) · [English](README_EN.md) · [日本語](README_JA.md)

</div>

<div align="center">

🎯 **Workflows d’agents intelligents** &nbsp;•&nbsp; 📊 **Visualisation interactive des données**<br>
🤖 **Génération automatique de code** &nbsp;•&nbsp; 📈 **Évaluation de bout en bout**

[⭐ Star the repo](https://github.com/usail-hkust/dslighting/stargazers) &nbsp;•&nbsp; [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## 📸 Aperçu de l’interface Web

### Tableau de bord principal
![Main Dashboard](../assets/web_ui_main_page.png)

### Analyse exploratoire (EDA)
![EDA](../assets/web_ui_eda.png)

### Tâches personnalisées
![Custom Tasks](../assets/web_ui_user_custome_task.png)

### Entraînement de modèle
![Model Training](../assets/web_ui_model_training.png)

### Génération de rapport
![Report Generation](../assets/web_ui_report.png)

---

## 📖 Présentation

DSLIGHTING est un système full-stack de workflow data science avec des workflows de type agent et une structure de données réutilisable pour l’exécution, l’évaluation et l’itération des tâches.

### ✨ Fonctionnalités clés

- 🤖 **Plusieurs workflows d’agents** : aide, automind, dsagent, etc.
- 🔄 **Cadre de méta‑optimisation** : AFlow pour sélectionner automatiquement le meilleur workflow
- 📊 **Interface Web de visualisation** : tableau de bord Next.js + FastAPI
- 📝 **Journalisation complète** : enregistre les artefacts et les résumés de chaque exécution
- 🧩 **Architecture extensible** : registre de tâches et préparation des données flexibles
- 📦 **Contexte de paquets intelligent** (v1.4.0+) : détecte les paquets disponibles pour éviter le code incompatible
- 🎯 **Jeux de données intégrés** (v1.8.1+) : exemples prêts à l’emploi sans préparation

---

## 🆕 Expérience rapide

### Étape 1 : Installer DSLighting

```bash
# Créer un environnement virtuel (recommandé)
python3 -m venv dslighting-env
source dslighting-env/bin/activate  # Windows: dslighting-env\Scripts\activate

# Installer DSLighting
pip install dslighting
```

### Étape 2 : Configurer les clés API

Créez un fichier `.env` et définissez vos clés :

```bash
# .env
API_KEY=sk-your-api-key-here
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

**Fournisseurs pris en charge** :
- **OpenAI** : https://openai.com/ - API Base: `https://api.openai.com/v1`
- **Zhipu AI** (recommandé en Chine) : https://bigmodel.cn/ - API Base: `https://open.bigmodel.cn/api/paas/v4`
- **SiliconFlow** : https://siliconflow.cn/ - API Base: `https://api.siliconflow.cn/v1`

### Étape 3 : Choisir un mode d’utilisation

---

**🌱 Mode débutant (recommandé)**

#### Option 1 : Jeu de données intégré (zéro configuration)

**Aucune préparation des données, exécution en une ligne !**

```python
# run_builtin.py
from dotenv import load_dotenv
load_dotenv()

import dslighting

# Utiliser un jeu de données intégré sans configurer de chemin
result = dslighting.run_agent(task_id="bike-sharing-demand")

print(f"✅ Terminé ! Score: {result.score}")
```

**Jeu de données intégré** :
- `bike-sharing-demand` - Prévision de la demande de vélos
- ✅ Contient train/test/answers complets
- ✅ Prêt à l’emploi
- ✅ Idéal pour une prise en main rapide

#### Option 2 : API ouverte (recommandée pour débutants)

**Trois fonctions : analyser, traiter, modéliser**

```python
import dslighting

# Analyze - explorer les données (2 itérations, conserver l’espace de travail)
result = dslighting.analyze(
    data="./data/titanic",
    description="Analyser la distribution des passagers",
    model="gpt-4o"
)

# Process - nettoyer les données (3 itérations, conserver l’espace de travail)
result = dslighting.process(
    data="./data/titanic",
    description="Traiter les valeurs manquantes et les outliers",
    model="gpt-4o"
)

# Model - entraîner un modèle (4 itérations, conserver l’espace de travail)
result = dslighting.model(
    data="./data/titanic",
    description="Entraîner un modèle de prédiction de survie",
    model="gpt-4o"
)
```

**Points forts** :
- 🎯 **Simple et intuitif** : trois API pour les tâches courantes
- 🔄 **Itérations automatiques** : paramètres par défaut adaptés
- 📁 **Conservation des résultats** : espace de travail et fichiers sauvegardés

📖 **Tutoriel complet** : [examples/open_ended_demo/README.md](../examples/open_ended_demo/README.md)

---

**🚀 Mode avancé (pour utilisateurs expérimentés)**

#### Option 3 : Configuration globale

**Configurer une fois, réutiliser partout**

```python
import dslighting

# Configurer les répertoires de données et de registre
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

# Ensuite, fournir uniquement task_id
agent = dslighting.Agent()
result = agent.run(task_id="my-custom-task")
```

**Avantages** :
- 🔧 **Gestion centralisée** de plusieurs tâches
- 📊 **Traitement en lot** pour de nombreuses compétitions
- ⚡ **Efficacité** avec moins de configuration répétée

#### Option 4 : Définir un Agent personnalisé (expert)

**Construire un Agent sur mesure avec contrôle total**

**Exemple : créer un Agent personnalisé**

```python
from dslighting.operators.custom import SimpleOperator

# 1. Définir un opérateur (capacité réutilisable)
async def summarize(text: str) -> dict:
    return {"summary": text[:200]}

summarize_op = SimpleOperator(func=summarize, name="Summarize")

# 2. Définir un workflow (chaîner les opérateurs)
class MyWorkflow:
    def __init__(self, operators):
        self.ops = operators

    async def solve(self, description, io_instructions, data_dir, output_path):
        _ = await self.ops["summarize"](text=description)

# 3. Créer une factory (construire le workflow)
class MyWorkflowFactory:
    def __init__(self, model="openai/gpt-4o"):
        self.model = model

    def create_agent(self):
        operators = {"summarize": summarize_op}
        return MyWorkflow(operators)

# 4. Utiliser l’Agent personnalisé
agent = MyWorkflowFactory(model="openai/deepseek-ai/DeepSeek-V3.1-Terminus").create_agent()
```

**Concepts clés** :
- **Operator** : capacité atomique réutilisable (analyse, modélisation, visualisation)
- **Workflow** : enchaîne les opérateurs pour résoudre une tâche
- **Factory** : construit et configure l’agent

**Cas d’usage** :
- 🎯 Logique d’exécution spécifique
- 🔬 Recherche sur de nouvelles architectures d’agents
- 🧩 Composition de capacités spécialisées
- 📈 Optimisation de workflows métier

**Bonnes pratiques** :
- ✅ Sorties flexibles : rapports, graphiques, modèles
- ✅ Exécution en sandbox pour la sécurité
- ✅ Préférer des opérateurs petits et composables

📖 **Tutoriel complet** : [AdvancedDSAgent examples](https://github.com/usail-hkust/dslighting/tree/main/examples/advanced_custom_agent)

---

## 🚀 Quick Start

### Exigences système

- **Python** : 3.10 ou plus
  ```bash
  # Vérifier la version Python
  python --version
  # ou
  python3 --version
  ```
- **Node.js** : 18.x ou plus
  ```bash
  # Vérifier la version Node.js
  node --version
  ```
- **npm** : 9.x ou plus (fourni avec Node.js)
  ```bash
  # Vérifier la version npm
  npm --version
  ```
- **Git** : gestion de version

### 1. Préparer l’environnement

```bash
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting
python3.10 -m venv dslighting
source dslighting/bin/activate  # Windows: dslighting\Scripts\activate
```

### 2. Installer les dépendances

**Installation standard** (recommandée) :
```bash
pip install -r requirements.txt
```

**Option alternative** (si la standard échoue) :
```bash
pip install -r requirements_local.txt
```

> 💡 **Notes** :
> - `requirements.txt` : versions verrouillées, pour production
> - `requirements_local.txt` : versions flexibles, pour développement

### 3. Configurer les clés API

```bash
cp .env.example .env
# Éditez .env pour renseigner vos clés
```

DSLighting prend en charge plusieurs fournisseurs LLM :

**Fournisseurs en Chine** (recommandé pour les utilisateurs en Chine) :
- **Zhipu AI** (https://bigmodel.cn/) - modèles GLM
  - API Base: `https://open.bigmodel.cn/api/paas/v4`
  - Obtenir une clé : https://open.bigmodel.cn/usercenter/apikeys
- **SiliconFlow** (https://siliconflow.cn/) - DeepSeek, Qwen, etc.
  - API Base: `https://api.siliconflow.cn/v1`
  - Obtenir une clé : https://siliconflow.cn/account/ak

**Fournisseurs internationaux** :
- **OpenAI** (https://openai.com/) - modèles GPT
  - API Base: `https://api.openai.com/v1`
  - Obtenir une clé : https://platform.openai.com/api-keys

Vous pouvez définir `API_KEY` / `API_BASE` ou fournir des réglages par modèle via `LLM_MODEL_CONFIGS`.

> 💡 **Exemples de configuration** : consultez `.env.example` pour les configs multi-modèles, rotation de clés, température, etc.

### 4. Préparer les données

DSLighting supporte plusieurs sources de données :

#### Méthode 1 : Télécharger via MLE-Bench (recommandé)

[MLE-Bench](https://github.com/openai/mle-bench) est un benchmark d’évaluation ML fourni par OpenAI.

```bash
# 1. Cloner le dépôt MLE-Bench
git clone https://github.com/openai/mle-bench.git
cd mle-bench

# 2. Installer les dépendances
pip install -e .

# 3. Télécharger tous les datasets
python scripts/prepare.py --competition all

# 4. Lier les données au projet DSLighting
# Les données MLE-Bench sont téléchargées dans ~/mle-bench/data/
ln -s ~/mle-bench/data/competitions /path/to/dslighting/data/competitions
```

> 📖 **Plus d’infos** : [MLE-Bench GitHub](https://github.com/openai/mle-bench)

#### Méthode 2 : Dataset personnalisé

Organisez vos données selon la structure DSLighting :

```
data/competitions/
  <competition-id>/
    config.yaml           # Config de compétition
    prepared/
      public/            # Données publiques
      private/           # Données privées
```

> 💡 **Note** : d’autres types de données et modèles pré-entraînés arrivent bientôt.

> 📖 **Guide de préparation** : [DATA_PREPARATION.md](DATA_PREPARATION.md)

### 5. Lancer une tâche

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --data-dir data/competitions \
  --task-id bike-sharing-demand \
  --llm-model gpt-4
```

### 6. Web UI (recommandée)

Interface web Next.js + FastAPI pour un upload et une exécution facilités.

#### 6.1 Configuration du backend

```bash
source dslighting/bin/activate
# Installer les dépendances backend
pip install -r web_ui/backend/requirements.txt
```

#### 6.2 Démarrer le backend

```bash
cd web_ui/backend
python main.py
```

Ou avec uvicorn :

```bash
cd web_ui/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

> 📖 **Documentation** : [Backend README](../../web_ui/backend/README.md)

> 💡 **Astuce** : le backend tourne sur **8003** par défaut. Modifiez `main.py` si besoin.

#### 6.3 Démarrer le frontend

```bash
cd web_ui/frontend
npm install
npm run dev
```

> 📖 **Documentation** : [Frontend README](../../web_ui/frontend/README.md)

#### 6.4 Accéder au dashboard

Ouvrez : [http://localhost:3000](http://localhost:3000)

---

## 🏗️ Core Features

### Workflows d’agents

- **`aide`** : boucle itérative de génération et revue de code
- **`automind`** : planification + raisonnement avec mémoire et décomposition
- **`dsagent`** : boucle plan/exécution structurée
- **`data_interpreter`** : exécution rapide et débogage
- **`autokaggle`** : workflow Kaggle en mode SOP
- **`aflow`** : méta‑optimisation de workflows
- **`deepanalyze`** : workflow axé analyse

### Structure des données

```
data/competitions/
  <competition-id>/
    config.yaml           # Config de compétition
    prepared/
      public/            # Données publiques
      private/           # Données privées
```

### Configuration

`config.yaml` est lu par les runners de benchmark et le service LLM :

- `competitions` : liste par défaut MLEBench
- `sciencebench_competitions` (optionnel) : liste par défaut ScienceBench
- `custom_model_pricing` : override des prix LiteLLM
- `run` : options de journalisation des traces

### Tarification des modèles personnalisée

**Comportement par défaut** :
- DSLighting utilise la tarification par défaut de LiteLLM
- Sans `config.yaml`, le système fonctionne (pas d’erreur)
- La tarification est optionnelle et ne sert qu’à surcharger

**Tarification personnalisée** :

Pour définir les prix de modèles spécifiques, créez `config.yaml` à la racine du projet :

**Emplacements** :
```bash
# Pour une installation pip
/path/to/your/project/config.yaml

# Exemple dans un projet de test
/Users/liufan/Applications/Github/dslighting_test_project/config.yaml
```

> 📖 **Exemple** : [config.yaml.example](../config.yaml.example)

**Exemple** :
```yaml
custom_model_pricing:
  openai/Qwen/Qwen3-Coder-480B-A35B-Instruct:
    input_cost_per_token: 6.0e-07
    output_cost_per_token: 1.8e-06
  openai/Qwen/Qwen3-Coder-30B-A3B-Instruct:
    input_cost_per_token: 6.0e-07
    output_cost_per_token: 1.8e-06
  o4-mini-2025-04-16:
    input_cost_per_token: 1.1e-06
    output_cost_per_token: 4.4e-06
  openai/deepseek-ai/DeepSeek-V3.1-Terminus:
    input_cost_per_token: 5.55e-07
    output_cost_per_token: 1.67e-06
```

**Paramètres** :
- `input_cost_per_token` : prix par token d’entrée (par requête)
- `output_cost_per_token` : prix par token de sortie (par réponse)
- Unité : USD/token (souvent en notation scientifique)

**Notes** :
- 💡 La tarification est optionnelle et ne déclenche pas d’erreur
- 💡 Surcharger uniquement les modèles nécessaires
- 💡 Impacte le calcul de coût et le budget

---

## 📂 Logs et artefacts

Par défaut, les logs sont écrits dans :

```
runs/benchmark_results/<workflow>_on_<benchmark>/<model_name>/
```

Vous pouvez modifier la base avec `--log-path`.

---

## ❓ FAQ

Voir `FAQ.md` pour plus d’informations.

---

## ⭐ Star History

<div align="center">

<p>
  <a href="https://github.com/usail-hkust/dslighting/stargazers"><img src="../assets/roster/stargazers.svg" alt="Stargazers"/></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/network/members"><img src="../assets/roster/forkers.svg" alt="Forkers"/></a>
</p>

<a href="https://www.star-history.com/#usail-hkust/dslighting&type=timeline&legend=top-left">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&theme=dark&legend=top-left" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&legend=top-left" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&legend=top-left" />
  </picture>
</a>

</div>

---

## 💬 Communauté WeChat

Rejoignez notre groupe WeChat pour échanger avec les utilisateurs et développeurs !

<div align="center">

<img src="../assets/wechat_group.jpg" alt="WeChat Group" width="300" style="border-radius: 10px; border: 2px solid #e0e0e0;">

**Scannez le QR code ci‑dessus pour rejoindre la communauté**

</div>

Dans le groupe, vous pouvez :
- 🤝 Échanger des expériences et conseils
- 💡 Proposer des fonctionnalités et feedbacks
- 🐛 Signaler des bugs et obtenir de l’aide
- 📢 Suivre les dernières nouveautés

---

## 🤝 Contribuer

<div align="center">

Nous espérons que DSLIGHTING deviendra un cadeau pour la communauté. 🎁

<a href="https://github.com/usail-hkust/dslighting/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=usail-hkust/dslighting" />
</a>

**Contributeurs principaux** :
- [luckyfan-cs](https://github.com/luckyfan-cs) (chef de projet, développement front & back)
- [canchengliu](https://github.com/canchengliu) (contribution aux workflows)

Voir `CONTRIBUTING.md` pour plus de détails.

</div>

---

## 🔗 Communauté

<div align="center">

**[DSLIGHTING Community](https://github.com/luckyfan-cs)**

[💬 WeChat Group](#-communauté-wechat) · [⭐ Star us](https://github.com/usail-hkust/dslighting/stargazers) · [🐛 Report a bug](https://github.com/usail-hkust/dslighting/issues) · [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## 📄 Licence

Ce projet est sous licence AGPL-3.0.

---

## 🙏 Remerciements

Merci de votre visite sur DSLIGHTING !

---

## 📊 Statistiques du projet

![](https://komarev.com/ghpvc/?username=usail-hkust&repo=dslighting&style=for-the-badge)
![](https://img.shields.io/github/issues/usail-hkust/dslighting?style=for-the-badge)
![](https://img.shields.io/github/forks/usail-hkust/dslighting?style=for-the-badge)
![](https://img.shields.io/github/stars/usail-hkust/dslighting?style=for-the-badge)

---

## 📚 Citation

Si vous utilisez DSLIGHTING dans vos travaux, veuillez citer :

```bibtex
@software{dslighting2025,
  title = {DSLIGHTING: An End-to-End Data Science Intelligent Assistant System},
  author = {Liu, F. and Liu, C. and others},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/usail-hkust/dslighting},
  version = {1.0.0}
}
```

Ou en texte simple :

```
Liu, F., Liu, C., et al. (2025). DSLIGHTING: An End-to-End Data Science Intelligent Assistant System.
GitHub repository. https://github.com/usail-hkust/dslighting
```
