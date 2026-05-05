import os
import random
import time
from pathlib import Path

import joblib
import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from api.database import init_db, log_prediction, get_history_7days, get_daily_aggregates_7days, get_anomalies_7days
from error_handlers import (
    register_error_handlers, validate_sensor_data,
    ModelError, DatabaseError, InvalidSensorData, logger
)

BASE_DIR   = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"

app = FastAPI()
REQUEST_COUNT = Counter(
    "irrigation_api_requests_total",
    "Total HTTP requests received by the irrigation API.",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "irrigation_api_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "endpoint"],
)
PREDICTION_COUNT = Counter(
    "irrigation_predictions_total",
    "Total predictions grouped by irrigation decision.",
    ["irrigation_needed"],
)


@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    endpoint = request.url.path
    REQUEST_LATENCY.labels(request.method, endpoint).observe(time.perf_counter() - start)
    REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
register_error_handlers(app)   # ← branche tous les handlers d'erreur
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Chargement du modèle ──────────────────────────────────────────────────────
try:
    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    logger.info("Modèle et scaler chargés avec succès.")
except Exception as e:
    logger.critical(f"Impossible de charger le modèle : {e}")
    model  = None
    scaler = None


# ─── Démarrage ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    init_db()


# ─── Schéma de requête ─────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    soil_moisture:  float
    temperature:    float
    humidity:       float
    rainfall:       float
    sunlight_hours: float


# ─── Page d'accueil ────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Prédiction d'irrigation</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; }
            h1 { color: #2b6cb0; }
            label { display: block; margin-top: 16px; font-weight: 600; }
            input { width: 100%; padding: 10px; margin-top: 6px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            button { margin-top: 20px; padding: 12px 20px; background: #2b6cb0; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #234e92; }
            .result  { margin-top: 24px; padding: 18px; background: #f0f8ff; border: 1px solid #bee3f8; border-radius: 6px; }
            .error   { margin-top: 24px; padding: 18px; background: #fff0f0; border: 1px solid #ffb3b3; border-radius: 6px; color: #c0392b; }
            #anomaly-alert { background: #ff6b6b; color: white; padding: 15px; border-radius: 5px; margin-top: 10px; }
            #load-history-btn, #simulate-btn {
                padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; color: white; margin-top: 12px;
            }
            #load-history-btn { background: #28a745; }
            #load-history-btn:hover { background: #218838; }
            #simulate-btn { background: #6f42c1; }
            #simulate-btn:hover { background: #5a32a3; }
            .sim-box { margin-top: 16px; padding: 14px; background: #f3eeff; border: 1px solid #c4a8f5; border-radius: 6px; font-size: 14px; }
        </style>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>Prédiction d'irrigation</h1>
        <p>Remplissez les valeurs ci-dessous puis cliquez sur <strong>Prédire</strong>.</p>
        <form id="predict-form">
            <label>Soil Moisture (%) — entre 0 et 100<input type="number" step="0.01" id="soil_moisture" required></label>
            <label>Temperature (°C) — entre -20 et 60<input type="number" step="0.01" id="temperature" required></label>
            <label>Humidity (%) — entre 0 et 100<input type="number" step="0.01" id="humidity" required></label>
            <label>Rainfall (mm) — entre 0 et 500<input type="number" step="0.01" id="rainfall" required></label>
            <label>Sunlight Hours — entre 0 et 24<input type="number" step="0.01" id="sunlight_hours" required></label>
            <button type="submit">Prédire</button>
        </form>
        <div id="result"></div>

        <div style="margin-top:40px;">
            <h2>🧪 Test — Simulation capteur</h2>
            <p>Génère des données aléatoires sans matériel réel.</p>
            <button id="simulate-btn">Simuler un capteur</button>
            <div id="sim-result" class="sim-box" style="display:none;"></div>
        </div>

        <div style="margin-top:40px;">
            <h2>📊 Historique + analyse</h2>
            <button id="load-history-btn">Charger analyse</button>
            <div id="water-chart"></div>
            <div id="freq-chart"></div>
            <div id="anomaly-alert" style="display:none;"></div>
        </div>

        <script>
        // Affiche une erreur proprement dans le div cible
        function showError(divId, message) {
            const div = document.getElementById(divId);
            div.className = 'error';
            div.style.display = 'block';
            div.innerHTML = '❌ ' + message;
        }

        document.addEventListener("DOMContentLoaded", function () {

            // ── Prédiction manuelle ──────────────────────────────────────────
            document.getElementById('predict-form').addEventListener('submit', async function (e) {
                e.preventDefault();
                const resultDiv = document.getElementById('result');
                resultDiv.className = 'result';
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = "⏳ Chargement...";

                const payload = {
                    soil_moisture:  Number(document.getElementById('soil_moisture').value),
                    temperature:    Number(document.getElementById('temperature').value),
                    humidity:       Number(document.getElementById('humidity').value),
                    rainfall:       Number(document.getElementById('rainfall').value),
                    sunlight_hours: Number(document.getElementById('sunlight_hours').value)
                };

                try {
                    const response = await fetch('/predict', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                    const data = await response.json();

                    // Erreur métier renvoyée par le serveur (422, 500…)
                    if (!response.ok) {
                        showError('result', data.detail || 'Erreur inconnue');
                        return;
                    }

                    const color = data.irrigation_needed === 1 ? 'green' : 'red';
                    let html = `<h3 style="color:${color}">${data.message}</h3>`;
                    if (data.importance) {
                        html += '<h4>📊 Importance des facteurs :</h4>';
                        for (let key in data.importance) {
                            html += `${key}: ${(data.importance[key] * 100).toFixed(1)}%<br>`;
                        }
                    }
                    resultDiv.innerHTML = html;

                } catch (error) {
                    showError('result', 'Impossible de joindre le serveur.');
                }
            });

            // ── Simulation capteur ───────────────────────────────────────────
            document.getElementById('simulate-btn').addEventListener('click', async function () {
                const simDiv = document.getElementById('sim-result');
                simDiv.style.display = 'block';
                simDiv.className = 'sim-box';
                simDiv.innerHTML = '⏳ Simulation en cours...';

                try {
                    const res = await fetch('/test/simulate');
                    const data = await res.json();

                    if (!res.ok) {
                        simDiv.className = 'error';
                        simDiv.innerHTML = '❌ ' + (data.detail || 'Erreur de simulation');
                        return;
                    }

                    const inp   = data.simulated_input;
                    const color = data.irrigation_needed === 1 ? 'green' : 'red';
                    let html = `<strong>Données simulées :</strong><br>
                        💧 Sol: ${inp.soil_moisture}% &nbsp;|&nbsp;
                        🌡️ Temp: ${inp.temperature}°C &nbsp;|&nbsp;
                        💦 Hum: ${inp.humidity}% &nbsp;|&nbsp;
                        🌧️ Pluie: ${inp.rainfall}mm &nbsp;|&nbsp;
                        ☀️ Soleil: ${inp.sunlight_hours}h<br><br>
                        <span style="color:${color};font-weight:600">${data.message}</span>`;
                    if (data.importance) {
                        html += '<br><br><strong>Importance :</strong><br>';
                        for (let key in data.importance) {
                            html += `${key}: ${(data.importance[key] * 100).toFixed(1)}%<br>`;
                        }
                    }
                    simDiv.innerHTML = html;

                } catch (e) {
                    simDiv.className = 'error';
                    simDiv.innerHTML = '❌ Impossible de joindre le serveur.';
                }
            });

            // ── Historique & analyse ─────────────────────────────────────────
            document.getElementById('load-history-btn').addEventListener('click', loadAnalysis);
        });

        async function loadAnalysis() {
            const loadBtn = document.getElementById('load-history-btn');
            loadBtn.textContent = 'Chargement...';

            try {
                const res  = await fetch('/analysis');
                const data = await res.json();

                if (!res.ok) {
                    document.getElementById('water-chart').innerHTML =
                        '<p style="color:red">❌ ' + (data.detail || 'Erreur') + '</p>';
                    return;
                }

                if (data.length === 0) {
                    document.getElementById('water-chart').innerHTML = '<p>Aucune donnée disponible.</p>';
                    return;
                }

                const dates = data.map(d => d.date).reverse();
                const water = data.map(d => d.total_water || 0).reverse();
                const freq  = data.map(d => d.irrigation_count || 0).reverse();

                Plotly.newPlot('water-chart',
                    [{ x: dates, y: water, type: 'bar' }],
                    { title: "Consommation d'eau 💧" }
                );
                Plotly.newPlot('freq-chart',
                    [{ x: dates, y: freq, type: 'scatter', mode: 'lines+markers' }],
                    { title: 'Fréquence irrigation' }
                );

                const anomRes    = await fetch('/anomalies');
                const anomalies  = await anomRes.json();
                const alertDiv   = document.getElementById('anomaly-alert');

                if (anomalies.length > 0) {
                    alertDiv.innerHTML     = `⚠️ ${anomalies.length} anomalie(s) détectée(s) sur soil_moisture`;
                    alertDiv.style.display = 'block';
                } else {
                    alertDiv.style.display = 'none';
                }

            } catch (e) {
                document.getElementById('water-chart').innerHTML =
                    '<p style="color:red">❌ Impossible de charger l\'analyse.</p>';
            }

            loadBtn.textContent = 'Actualiser analyse';
        }
        </script>
    </body>
    </html>
    """


# ─── Prédiction ────────────────────────────────────────────────────────────────
@app.post("/predict")
def predict(request: PredictRequest):
    # 1. Vérifier que le modèle est disponible
    if model is None or scaler is None:
        raise ModelError("Modèle non chargé.")

    # 2. Valider les valeurs physiques des capteurs
    validate_sensor_data(request.dict())

    # 3. Prédire
    try:
        input_data   = np.array([[
            request.soil_moisture, request.temperature,
            request.humidity, request.rainfall, request.sunlight_hours
        ]])
        input_scaled = scaler.transform(input_data)
        prediction   = int(model.predict(input_scaled)[0])
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction : {e}")
        raise ModelError(f"Prédiction impossible : {e}") from e

    # 4. Enregistrer (DatabaseError propagée automatiquement si ça échoue)
    log_prediction(request.dict(), prediction)

    importance = dict(zip(
        ["soil", "temp", "humidity", "rain", "sun"],
        model.feature_importances_
    ))
    message = (
        "Sol sec + température élevée → irrigation recommandée 💧"
        if prediction == 1 else
        "Conditions favorables → pas d'irrigation 🌱"
    )
    PREDICTION_COUNT.labels(str(prediction)).inc()
    return {"irrigation_needed": prediction, "message": message, "importance": importance}


# ─── Simulation capteur ────────────────────────────────────────────────────────
@app.get("/test/simulate")
def simulate_sensor():
    """Génère des capteurs aléatoires et retourne la prédiction du modèle."""
    if model is None or scaler is None:
        raise ModelError("Modèle non disponible pour la simulation.")

    fake_data = PredictRequest(
        soil_moisture=round(random.uniform(10, 90), 2),
        temperature=round(random.uniform(15, 45), 2),
        humidity=round(random.uniform(20, 95), 2),
        rainfall=round(random.uniform(0, 50), 2),
        sunlight_hours=round(random.uniform(0, 12), 2)
    )
    result = predict(fake_data)
    return {"simulated_input": fake_data.dict(), **result}


# ─── Historique ────────────────────────────────────────────────────────────────
@app.get("/history")
def get_history():
    return get_history_7days()


@app.get("/analysis")
def get_analysis():
    return get_daily_aggregates_7days()


@app.get("/anomalies")
def get_anomalies():
    return get_anomalies_7days()
