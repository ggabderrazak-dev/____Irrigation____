/**
 * api.js — Couche de communication avec ton FastAPI existant
 * Tous les appels correspondent aux endpoints de main.py
 *
 * BASE_URL : change selon ton environnement
 *   - Dev local  → "http://localhost:8000"
 *   - Docker     → "http://api:8000"  (ou le nom du service dans docker-compose)
 *   - Production → ton domaine réel
 */
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`);
  return data;
}

// POST /predict  ← correspond exactement à PredictRequest dans main.py
export async function predict(payload) {
  return request("/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// GET /test/simulate  ← endpoint existant dans main.py
export async function simulate() {
  return request("/test/simulate");
}

// GET /history  ← get_history_7days()
export async function getHistory() {
  return request("/history");
}

// GET /analysis  ← get_daily_aggregates_7days()
export async function getAnalysis() {
  return request("/analysis");
}

// GET /anomalies  ← get_anomalies_7days()
export async function getAnomalies() {
  return request("/anomalies");
}
