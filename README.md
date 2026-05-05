# Smart Irrigation - Projet MLOps / DevOps

Ce projet est une application complete de prediction d'irrigation intelligente. Il combine un modele de machine learning, une API FastAPI, une interface web React, une base de donnees SQLite, un pipeline d'entrainement reproductible, ainsi que des outils de monitoring et de conteneurisation.

L'objectif est d'aider a decider si une parcelle doit etre irriguee a partir de donnees capteurs et meteo: humidite du sol, temperature, humidite de l'air, pluie et heures d'ensoleillement.

## Fonctionnalites principales

- Prediction automatique du besoin d'irrigation avec un modele `RandomForestClassifier`.
- API REST FastAPI pour exposer le modele et les donnees d'historique.
- Interface web React/Vite avec plusieurs pages: tableau de bord, controle, planning, historique et parametres.
- Simulation de donnees capteurs pour tester le systeme sans materiel reel.
- Enregistrement des predictions dans une base SQLite locale.
- Analyse des donnees recentes: historique, consommation d'eau, frequence d'irrigation et detection d'anomalies.
- Pipeline ML reproductible avec DVC, parametres centralises et metriques JSON.
- Suivi des experiences avec MLflow.
- Monitoring API avec Prometheus et Grafana.
- Deploiement local avec Docker Compose.
- Tests automatises avec Pytest.
- CI avec GitHub Actions et Jenkinsfile.

## Architecture du projet

```text
.
|-- api/                         # Backend FastAPI et gestion SQLite
|   |-- main.py                  # Endpoints API, prediction, metrics Prometheus
|   |-- database.py              # Creation DB, logs, historique, agregations
|   `-- train_model.py           # Script d'entrainement cote API
|-- data/                        # Jeux de donnees utilises pour l'entrainement
|-- docs/                        # Documentation complementaire
|-- irrigation_frontend/         # Application React/Vite
|   |-- src/
|   |   |-- pages/               # Dashboard, Control, Schedule, History, Settings
|   |   |-- services/api.js      # Client HTTP vers FastAPI
|   |   `-- components/          # Composants UI
|   `-- package.json
|-- models/                      # Modele et scaler serialises
|   |-- model.pkl
|   `-- scaler.pkl
|-- monitoring/                  # Configuration Prometheus et Grafana
|-- src/                         # Pipeline ML, preprocessing, AutoML
|-- tests/                       # Tests API et base de donnees
|-- docker-compose.yml           # Lancement API, frontend, MLflow, Prometheus, Grafana
|-- Dockerfile                   # Image Docker du backend
|-- dvc.yaml                     # Pipeline DVC
|-- params.yaml                  # Parametres d'entrainement
`-- requirements.txt             # Dependances Python
```

## Donnees utilisees

Le modele utilise principalement les variables suivantes:

- `soil_moisture`: humidite du sol.
- `temperature`: temperature ambiante.
- `humidity`: humidite de l'air.
- `rainfall`: quantite de pluie.
- `sunlight_hours`: duree d'ensoleillement.

La cible predite est:

- `irrigation_needed`: `1` si l'irrigation est recommandee, `0` sinon.

Le fichier de donnees principal est `data/Smart_Farming_Crop_Yield_2024.csv`. Le pipeline normalise les noms de colonnes, construit la cible si elle est absente, separe les donnees en train/test, standardise les features, puis entraine un modele Random Forest.

## Backend FastAPI

Le backend se trouve dans `api/main.py`. Au demarrage, il charge:

- `models/model.pkl`
- `models/scaler.pkl`

Il initialise aussi la base SQLite `api/irrigation_history.db`, qui stocke les predictions effectuees.

### Endpoints principaux

- `GET /`  
  Page HTML simple integree au backend pour tester rapidement la prediction.

- `POST /predict`  
  Recoit les donnees capteurs et retourne la decision d'irrigation.

- `GET /test/simulate`  
  Genere des valeurs aleatoires realistes et lance une prediction.

- `GET /history`  
  Retourne les predictions enregistrees sur les 7 derniers jours.

- `GET /analysis`  
  Retourne les agregats journaliers: eau consommee et nombre d'irrigations.

- `GET /anomalies`  
  Detecte les anomalies sur l'humidite du sol avec une methode IQR.

- `GET /metrics`  
  Expose les metriques Prometheus de l'API.

## Frontend React/Vite

L'interface web se trouve dans `irrigation_frontend`. Elle communique avec l'API via `src/services/api.js`.

Pages disponibles:

- Dashboard: vue generale de l'etat du systeme.
- Control: prediction manuelle et simulation capteur.
- Schedule: gestion ou visualisation de la planification.
- History: affichage de l'historique et des analyses.
- Settings: configuration de l'interface.

La variable `VITE_API_URL` permet de configurer l'URL du backend.

## Pipeline Machine Learning

Le pipeline principal est `src/train_pipeline.py`. Il utilise les parametres de `params.yaml`:

```yaml
train:
  data_path: data/Smart_Farming_Crop_Yield_2024.csv
  model_path: models/model.pkl
  scaler_path: models/scaler.pkl
  metrics_path: metrics.json
  test_size: 0.2
  random_state: 42
  n_estimators: 200
```

Etapes du pipeline:

1. Lecture du dataset.
2. Normalisation des noms de colonnes.
3. Creation de la cible `irrigation_needed` si elle n'existe pas.
4. Separation train/test.
5. Standardisation avec `StandardScaler`.
6. Entrainement d'un `RandomForestClassifier`.
7. Calcul des metriques `accuracy` et `f1`.
8. Sauvegarde du modele et du scaler dans `models/`.
9. Enregistrement des metriques dans `metrics.json`.
10. Journalisation de l'experience avec MLflow.

## DVC et reproductibilite

Le fichier `dvc.yaml` definit un stage `train`:

```bash
dvc repro
```

Cette commande relance l'entrainement en utilisant les dependances et sorties declarees:

- entree: `data/Smart_Farming_Crop_Yield_2024.csv`
- script: `src/train_pipeline.py`
- sorties: `models/model.pkl`, `models/scaler.pkl`
- metriques: `metrics.json`

## MLflow

MLflow est utilise pour suivre les experiences d'entrainement:

- parametres du modele,
- metriques,
- artefacts,
- modele scikit-learn journalise.

Avec Docker Compose, l'interface MLflow est disponible sur:

```text
http://localhost:5000
```

Les runs sont stockes localement dans le dossier `mlruns`.

## Monitoring

Le projet integre Prometheus et Grafana.

Prometheus collecte les metriques exposees par FastAPI sur `/metrics`, notamment:

- nombre total de requetes API,
- latence des requetes,
- nombre de predictions par decision d'irrigation.

URLs par defaut avec Docker Compose:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

La configuration se trouve dans `monitoring/`.

## Installation locale

### 1. Installer les dependances Python

```bash
python -m pip install -r requirements.txt
```

### 2. Lancer l'API FastAPI

```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

API disponible sur:

```text
http://127.0.0.1:8000
```

### 3. Lancer le frontend

```bash
cd irrigation_frontend
npm install
npm run dev
```

Interface disponible sur:

```text
http://localhost:5173
```

## Lancement avec Docker Compose

Pour lancer toute la stack:

```bash
docker compose up --build
```

Services exposes:

- API FastAPI: `http://localhost:8000`
- Frontend React: `http://localhost:5173`
- MLflow: `http://localhost:5000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Tests

Les tests se trouvent dans `tests/`.

Pour lancer les tests:

```bash
pytest
```

Les tests couvrent notamment:

- les endpoints FastAPI,
- la validation des donnees capteurs,
- les erreurs modele/base de donnees,
- les endpoints d'historique et d'analyse.

## Fichiers importants

- `api/main.py`: coeur de l'API et endpoints.
- `api/database.py`: gestion de la base SQLite.
- `error_handlers.py`: erreurs metier, validation et handlers FastAPI.
- `src/train_pipeline.py`: pipeline ML principal.
- `params.yaml`: configuration de l'entrainement.
- `dvc.yaml`: pipeline DVC.
- `models/model.pkl`: modele entraine.
- `models/scaler.pkl`: scaler utilise avant prediction.
- `irrigation_frontend/src/services/api.js`: communication frontend/backend.
- `docker-compose.yml`: orchestration de la stack.

## Notes de maintenance

- Ne pas versionner `node_modules`, les fichiers `__pycache__`, les logs, les bases SQLite locales et les runs MLflow.
- La base `api/irrigation_history.db` est locale et peut etre recreee par l'API, mais sa suppression efface l'historique.
- Le dossier `mlruns` contient l'historique des experiences MLflow.
- Si le modele ou le scaler sont absents, l'API demarre mais les endpoints de prediction renverront une erreur modele.

## Documentation complementaire

Voir aussi:

- `docs/CONCEPTS_INTEGRES.md`
- `irrigation_frontend/INTEGRATION_GUIDE.md`
