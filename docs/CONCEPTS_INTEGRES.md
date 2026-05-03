# Concepts integres dans le projet Smart Irrigation AI

## FastAPI

Le backend principal est `api/main.py`. Il sert le modele via `/predict`, expose l'historique via `/history`, l'analyse via `/analysis`, les anomalies via `/anomalies`, et le monitoring via `/metrics`.

## Git

Le projet est deja un depot Git. Les nouveaux fichiers ajoutent une structure plus professionnelle pour suivre le code, les pipelines, la CI et la configuration.

## DVC

Le fichier `dvc.yaml` decrit un pipeline de training reproductible:

```bash
dvc repro
```

Les hyperparametres sont centralises dans `params.yaml`, et les resultats sont ecrits dans `metrics.json`.

## MLflow

Le script `src/train_pipeline.py` loggue les parametres, les metriques et le modele dans MLflow.

```bash
python src/train_pipeline.py
mlflow ui
```

L'interface MLflow est aussi disponible avec Docker Compose sur `http://localhost:5000`.

## Prometheus et Grafana

FastAPI expose `/metrics`. Prometheus scrape ces metriques avec `monitoring/prometheus.yml`, puis Grafana charge automatiquement un dashboard simple.

```bash
docker compose up --build
```

URLs utiles:

- API: `http://localhost:8000`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Jenkins

Le fichier `Jenkinsfile` definit un pipeline CI:

- installation des dependances
- execution des tests
- build de l'image Docker

## DevOps

Le projet contient maintenant:

- `Dockerfile` pour l'API
- `irrigation_frontend/Dockerfile` pour le frontend
- `docker-compose.yml` pour lancer API, frontend, MLflow, Prometheus et Grafana
- `.github/workflows/ci.yml` pour une CI GitHub Actions
- `Jenkinsfile` pour Jenkins

## AutoML

Le fichier `src/automl_train.py` implemente un AutoML leger avec `GridSearchCV` pour tester automatiquement plusieurs hyperparametres du modele RandomForest.

```bash
python src/automl_train.py
```

## Spark

Le fichier `spark_profile.py` est un exemple optionnel d'analyse distribuee des donnees avec PySpark. Il sert surtout si le dataset devient volumineux.

```bash
python spark_profile.py
```

Pour l'utiliser, installe `pyspark` separement:

```bash
pip install pyspark
```

## Cloud Computing et Model-as-a-Service

Le modele est expose comme service via FastAPI. Avec Docker, il peut etre deploye sur un serveur cloud, Render, Railway, Azure, AWS, GCP ou une VM.

## Concepts non retenus comme dependance principale

- Flask: inutile ici car FastAPI fait deja le role API moderne.
- ZenML: possible, mais lourd pour ce projet. DVC + MLflow couvrent deja le pipeline et le tracking.
- DataOps complet: partiellement couvert par DVC, `params.yaml`, data CSV, et historique SQLite.
