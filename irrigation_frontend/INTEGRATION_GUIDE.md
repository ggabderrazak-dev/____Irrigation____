# Guide d'intégration — IrrigAI Frontend

## Structure finale du projet

```
IRRIGATION/
├── api/
│   ├── database.py          ← INCHANGÉ
│   ├── main.py              ← 2 PETITES MODIFICATIONS (voir ci-dessous)
│   └── static/              ← NOUVEAU : créé automatiquement par npm run build
│       └── (fichiers React compilés)
├── frontend/                ← NOUVEAU DOSSIER À CRÉER
│   ├── src/
│   │   ├── main.jsx
│   │   ├── tokens.css
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   └── UI.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Control.jsx
│   │   │   ├── Schedule.jsx
│   │   │   ├── History.jsx
│   │   │   └── Settings.jsx
│   │   ├── hooks/
│   │   │   └── useData.js
│   │   └── services/
│   │       └── api.js
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── models/
├── src/
├── tests/
├── error_handlers.py
└── main.py (racine — inutilisé si tu utilises api/main.py)
```

---

## ÉTAPE 1 — Créer le dossier frontend

```bash
# Depuis la racine de ton projet IRRIGATION/
mkdir frontend
cd frontend

# Copie tous les fichiers fournis dans ce dossier
# (package.json, vite.config.js, index.html, .env.example, src/)
```

---

## ÉTAPE 2 — Modifier api/main.py (2 changements seulement)

### Changement A : Ajouter le CORS middleware

```python
# AJOUTER ces imports en haut de api/main.py, après les imports existants
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# AJOUTER juste après app = FastAPI() :
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Dev React
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Changement B : Servir le build React (optionnel, pour production)

```python
# AJOUTER à la fin de api/main.py, APRÈS toutes tes routes :
import os
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
```

> ⚠ **Important** : le mount "/" doit être en DERNIER, après toutes les routes.
> La route GET "/" (page HTML actuelle) sera remplacée par l'app React en production.

### Résultat dans api/main.py :

```python
# ... imports existants ...
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)

# ... tout le reste INCHANGÉ ...

# Tout à la fin :
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
```

---

## ÉTAPE 3 — database.py → AUCUN CHANGEMENT

Ton database.py est parfait tel quel. Le frontend appelle les endpoints existants :

| Endpoint FastAPI      | Fonction database.py            | Page frontend |
|-----------------------|---------------------------------|---------------|
| GET /test/simulate    | (random + predict)              | Dashboard     |
| POST /predict         | log_prediction()                | Contrôle      |
| GET /history          | get_history_7days()             | Historique    |
| GET /analysis         | get_daily_aggregates_7days()    | Historique    |
| GET /anomalies        | get_anomalies_7days()           | Historique    |

---

## ÉTAPE 4 — Installer et lancer le frontend

```bash
cd frontend

# Installer les dépendances (Node.js requis)
npm install

# Copier le fichier d'environnement
cp .env.example .env.local
# (pas besoin de modifier si FastAPI tourne sur localhost:8000)

# Lancer en mode développement
npm run dev
# → Ouvre http://localhost:5173
```

---

## ÉTAPE 5 — Lancer FastAPI en parallèle

```bash
# Dans un autre terminal, depuis la racine du projet :
uvicorn api.main:app --reload --port 8000

# Ou si tu utilises le main.py à la racine :
uvicorn main:app --reload --port 8000
```

---

## ÉTAPE 6 — Build pour production (optionnel)

```bash
cd frontend
npm run build
# → Génère api/static/ avec tous les fichiers compilés
# → FastAPI sert ensuite le React via app.mount("/", ...)
# → Une seule URL : http://localhost:8000
```

---

## Vérification rapide

Une fois les deux serveurs lancés :

1. Ouvre http://localhost:5173
2. Va dans **Dashboard** → tu vois des métriques qui se rafraîchissent toutes les 5s (via /test/simulate)
3. Va dans **Contrôle** → remplis le formulaire → clique Prédire (appel POST /predict réel)
4. Va dans **Historique** → les données apparaissent après au moins une prédiction
5. Va dans **Planification** → programmes locaux (pas de backend requis)
6. Va dans **Paramètres** → configuration UI (pas de backend requis)

---

## Dépendances à installer (Node.js)

```bash
node --version   # Doit être >= 18
npm --version    # Inclus avec Node.js
```

Télécharger Node.js : https://nodejs.org (LTS recommandé)

---

## Problèmes fréquents

### Erreur CORS
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173' has been blocked
```
→ Vérifie que tu as bien ajouté `CORSMiddleware` dans api/main.py (Étape 2A).

### "API hors ligne" dans la sidebar
→ FastAPI n'est pas démarré. Lance `uvicorn api.main:app --reload` dans un autre terminal.

### "Aucune donnée" dans Historique
→ Normal au premier lancement. Va dans **Contrôle** et fais au moins une prédiction.

### Module 'from sklearn.py' dans api/
→ Ce fichier a un nom invalide en Python (conflit avec scikit-learn).
   Renomme-le en `train_model.py` ou `sklearn_example.py`.

---

## Fichiers NON modifiés

- `api/database.py` ← intact
- `error_handlers.py` ← intact
- `src/preprocessing.py` ← intact
- `src/train.py` ← intact
- `models/model.pkl` ← intact
- `models/scaler.pkl` ← intact
- `tests/` ← intact
