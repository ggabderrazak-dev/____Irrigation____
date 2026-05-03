# Irrigation Project

## Démarrage du site web

1. Installer les dépendances :
```bash
C:/Users/DELL/AppData/Local/Programs/Python/Python313/python.exe -m pip install -r requirements.txt
```

2. Lancer le serveur FastAPI :
```bash
C:/Users/DELL/AppData/Local/Programs/Python/Python313/python.exe -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

3. Ouvrir dans le navigateur :

- `http://127.0.0.1:8000/`

## Fonctionnalités

- Page web avec formulaire pour entrer :
  - `soil_moisture`
  - `temperature`
  - `humidity`
  - `rainfall`
  - `sunlight_hours`
- Prédiction de `irrigation_needed`
- Modèle et scaler chargés depuis :
  - `models/model.pkl`
  - `models/scaler.pkl`

## Notes

- Le modèle est entraîné avec `RandomForestClassifier` dans le notebook `notebooks/Untitled1.ipynb`.
- Si le serveur tourne, la page web et l'API sont accessibles depuis la même URL.

## Concepts MLOps / DevOps ajoutes

Ce projet integre maintenant plusieurs concepts de l'expose:

- FastAPI pour servir le modele comme API.
- DVC avec `dvc.yaml` et `params.yaml` pour reproduire le training.
- MLflow pour suivre les experiences et les metriques.
- Prometheus + Grafana pour monitorer l'API.
- Docker Compose pour lancer API, frontend, MLflow, Prometheus et Grafana.
- Jenkinsfile et GitHub Actions pour la CI.
- AutoML leger avec `src/automl_train.py`.
- Spark optionnel avec `spark_profile.py`.

Voir le detail dans `docs/CONCEPTS_INTEGRES.md`.
