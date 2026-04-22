# TODO: Ajout Historique + Analyse Irrigation

## Plan Executé:
**Information Gathered:** App FastAPI de prédiction irrigation stateless. Pipeline preprocessing avec outlier detection. Pas de DB/history.

**Files à éditer:** api/main.py, requirements.txt. Nouveaux: api/database.py, src/utils.py.

**Étapes:**

### 1. Créer api/database.py
- [x] SQLite DB (irrigation_history.db)
- [x] Fcts log, get_history, aggregates, anomalies
- Table logs (timestamp, soil_moisture, temp, humidity, rainfall, sunlight_hours, irrigation_needed, water_used)
- Fcts: init_db(), log_prediction(dict), get_history_7days(), get_aggregates_7days(), detect_anomalies_recent()

### 2. Créer src/utils.py
- [x] Copier func outlier() IQR du notebook (detect_outliers)

### 3. Mettre à jour requirements.txt
- [x] Ajouter plotly==5.22.0

### 4. Editer api/main.py
- [ ] Imports DB/utils
- [ ] Dans /predict: après prediction, log_prediction + init_db()
- [ ] Nouveaux endpoints /history, /analysis, /anomalies
- [ ] HTML: Nouvelle section "3. Historique + analyse" avec Plotly graphs (eau 7j, freq), anomalies alert

### 5. Followup
- [ ] pip install -r requirements.txt
- [ ] uvicorn api.main:app --reload
- [ ] Tester predictions, vérifier DB/graphs/anomalies

**Progress:** 3/5 Étapes complètes
