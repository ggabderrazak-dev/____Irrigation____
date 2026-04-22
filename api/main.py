from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import joblib
import numpy as np
from api.database import init_db, log_prediction, get_history_7days, get_daily_aggregates_7days, get_anomalies_7days

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"

app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_db()

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

class PredictRequest(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float
    rainfall: float
    sunlight_hours: float

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang=\"fr\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>Prédiction d'irrigation</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; }
            h1 { color: #2b6cb0; }
            label { display: block; margin-top: 16px; font-weight: 600; }
            input { width: 100%; padding: 10px; margin-top: 6px; border: 1px solid #ccc; border-radius: 4px; }
            button { margin-top: 20px; padding: 12px 20px; background: #2b6cb0; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #234e92; }
            .result { margin-top: 24px; padding: 18px; background: #f0f8ff; border: 1px solid #bee3f8; border-radius: 6px; }\n            #history-section { margin-top: 40px; }\n            #water-chart, #freq-chart { width: 100%; height: 400px; }\n            #anomaly-alert { background: #ff6b6b; color: white; padding: 15px; border-radius: 5px; margin-top: 10px; }\n            #load-history-btn { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }\n            #load-history-btn:hover { background: #218838; }\n        </style>\n        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>\n    </head>
    <body>
        <h1>Prédiction d'irrigation</h1>
        <p>Remplissez les valeurs ci-dessous puis cliquez sur <strong>Prédire</strong>.</p>
        <form id=\"predict-form\">
            <label>Soil Moisture (%)<input type=\"number\" step=\"0.01\" id=\"soil_moisture\" required></label>
            <label>Temperature (°C)<input type=\"number\" step=\"0.01\" id=\"temperature\" required></label>
            <label>Humidity (%)<input type=\"number\" step=\"0.01\" id=\"humidity\" required></label>
            <label>Rainfall (mm)<input type=\"number\" step=\"0.01\" id=\"rainfall\" required></label>
            <label>Sunlight Hours<input type=\"number\" step=\"0.01\" id=\"sunlight_hours\" required></label>
            <button type=\"submit\">Prédire</button>
        </form>
        <div class=\"result\" id=\"result\" style=\"display:none;\"></div>
        <div id=\"history-section\">
            <h2>3. Historique + analyse</h2>
            <p>Graphiques des 7 derniers jours: consommation d\'eau 💧 et fréquence d\'irrigation</p>
            <button id=\"load-history-btn\">Charger analyse</button>
            <div id=\"water-chart\"></div>
            <div id=\"freq-chart\"></div>
            <div id=\"anomaly-alert\" style=\"display:none;\"></div>
        </div>
        <script>
document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById('predict-form');
    const resultDiv = document.getElementById('result');

    form.addEventListener('submit', async function (event) {
        event.preventDefault();

        resultDiv.style.display = 'block';
        resultDiv.innerHTML = "⏳ Chargement...";

        const payload = {
            soil_moisture: Number(document.getElementById('soil_moisture').value),
            temperature: Number(document.getElementById('temperature').value),
            humidity: Number(document.getElementById('humidity').value),
            rainfall: Number(document.getElementById('rainfall').value),
            sunlight_hours: Number(document.getElementById('sunlight_hours').value)
        };

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            console.log("DATA:", data);

            // ✅ MESSAGE + COULEUR
            let color = data.irrigation_needed === 1 ? "green" : "red";

            let html = `
                <h3 style="color:${color}">
                    ${data.message}
                </h3>
            `;

            // 🔥 IMPORTANCE (PRO)
            if (data.importance) {
                html += "<h4>📊 Importance des facteurs :</h4>";

                for (let key in data.importance) {
                    html += `
                        ${key}: ${(data.importance[key] * 100).toFixed(1)}% <br>
                    `;
                }
            }

            resultDiv.innerHTML = html;

        } catch (error) {
            console.error(error);
            resultDiv.innerHTML = "❌ Erreur serveur";
        }
    });

    // 🔥 CONNECT BUTTON ANALYSIS
    document.getElementById('load-history-btn')
        .addEventListener('click', loadAnalysis);
});


// ================= ANALYSIS =================
async function loadAnalysis() {
    const loadBtn = document.getElementById('load-history-btn');
    loadBtn.textContent = "Chargement...";

    try {
        const res = await fetch('/analysis');
        const data = await res.json();

        if (data.length === 0) {
            document.getElementById('water-chart').innerHTML = "<p>Aucune donnée</p>";
            return;
        }

        const dates = data.map(d => d.date).reverse();
        const water = data.map(d => d.total_water || 0).reverse();
        const freq = data.map(d => d.irrigation_count || 0).reverse();

        Plotly.newPlot('water-chart', [{
            x: dates,
            y: water,
            type: 'bar'
        }], {title: "Consommation d'eau 💧"});

        Plotly.newPlot('freq-chart', [{
            x: dates,
            y: freq,
            type: 'scatter',
            mode: 'lines+markers'
        }], {title: "Fréquence irrigation"});

        const anomRes = await fetch('/anomalies');
        const anomalies = await anomRes.json();

        const alertDiv = document.getElementById('anomaly-alert');

        if (anomalies.length > 0) {
            alertDiv.innerHTML = "⚠️ Anomalies détectées";
            alertDiv.style.display = "block";
        } else {
            alertDiv.style.display = "none";
        }

    } catch (e) {
        console.error(e);
        document.getElementById('water-chart').innerHTML = "<p>Erreur</p>";
    }

    loadBtn.textContent = "Actualiser analyse";
}
let impHTML = "<br><b>Importance :</b><br>";
for (let key in data.importance) {
    impHTML += key + ": " + data.importance[key].toFixed(2) + "<br>";
}

document.getElementById('result').innerHTML += impHTML;
</script>
    </body>
    </html>
    """

@app.post("/predict")
def predict(request: PredictRequest):
    input_data = np.array([[
        request.soil_moisture,
        request.temperature,
        request.humidity,
        request.rainfall,
        request.sunlight_hours
    ]])
    input_scaled = scaler.transform(input_data)
    result = model.predict(input_scaled)[0]
    log_prediction(request.dict(), int(result))
    prediction = int(result)
    importance = dict(zip(
    ["soil", "temp", "humidity", "rain", "sun"],
    model.feature_importances_
    ))
    if prediction == 1:
        message = "Sol sec + température élevée → irrigation recommandée 💧"
    else:
        message = "Conditions favorables → pas d’irrigation 🌱"

    return {
       "irrigation_needed": prediction,
       "message": message,
       "importance": importance
    }

@app.get("/history")
def get_history():
    return get_history_7days()

@app.get("/analysis")
def get_analysis():
    return get_daily_aggregates_7days()

@app.get("/anomalies")
def get_anomalies():
    return get_anomalies_7days()
