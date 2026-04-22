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
