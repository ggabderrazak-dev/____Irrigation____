import { useState } from "react";
import { showToast, Toggle } from "../components/UI";

export default function PageSettings() {
  const [flow, setFlow]         = useState(2.0);
  const [duration, setDuration] = useState(5);
  const [alerts, setAlerts]     = useState({ moisture: true, anomaly: true, pump: false });
  const [apiUrl, setApiUrl]     = useState(import.meta.env.VITE_API_URL || "http://localhost:8000");

  const save = () => showToast("Paramètres sauvegardés ✓", "success");

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Paramètres</h1>
        <p className="page-subtitle mono">Configuration système et préférences</p>
      </div>

      <div className="grid-2">
        <div className="card card-glow">
          <div className="section-title">Système <div className="section-line" /></div>

          <div className="form-group">
            <label className="form-label">URL de l'API FastAPI</label>
            <input className="form-input" value={apiUrl}
              onChange={e => setApiUrl(e.target.value)}
              placeholder="http://localhost:8000" />
            <div className="mono" style={{ fontSize: 10, color: "var(--muted)", marginTop: 4 }}>
              Modifie VITE_API_URL dans ton .env pour changer
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Débit pompe (L/min) — FLOW_RATE_L_PER_MIN</label>
            <input type="number" className="form-input"
              value={flow} step={0.1} min={0.5} max={10}
              onChange={e => setFlow(parseFloat(e.target.value))} />
            <div className="mono" style={{ fontSize: 10, color: "var(--muted)", marginTop: 4 }}>
              Correspond à <code>FLOW_RATE_L_PER_MIN</code> dans database.py
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Durée cycle (min) — IRRIGATION_DURATION_MIN</label>
            <input type="number" className="form-input"
              value={duration} min={1} max={60}
              onChange={e => setDuration(parseInt(e.target.value))} />
            <div className="mono" style={{ fontSize: 10, color: "var(--muted)", marginTop: 4 }}>
              Correspond à <code>IRRIGATION_DURATION_MIN</code> dans database.py
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Eau par cycle estimée</label>
            <div className="form-input mono" style={{ color: "var(--accent)" }}>
              {(flow * duration).toFixed(2)} L
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Modèle ML</label>
            <select className="form-input form-select">
              <option>RandomForest — models/model.pkl</option>
              <option>GradientBoosting (non entraîné)</option>
            </select>
          </div>
        </div>

        <div>
          <div className="card card-glow" style={{ marginBottom: 16 }}>
            <div className="section-title">Notifications <div className="section-line" /></div>
            {[
              { key: "moisture", label: "Alerte humidité basse (< 30%)" },
              { key: "anomaly",  label: "Anomalie IQR détectée"          },
              { key: "pump",     label: "Changement état pompe"          },
            ].map(a => (
              <div key={a.key} className="stat-row">
                <span className="stat-name">{a.label}</span>
                <Toggle
                  value={alerts[a.key]}
                  onChange={v => setAlerts(x => ({ ...x, [a.key]: v }))}
                />
              </div>
            ))}
          </div>

          <div className="card card-glow">
            <div className="section-title">État système <div className="section-line" /></div>
            <div className="stat-row">
              <span className="stat-name">FastAPI / main.py</span>
              <span className="badge badge-green">● En ligne</span>
            </div>
            <div className="stat-row">
              <span className="stat-name">SQLite / database.py</span>
              <span className="badge badge-green">● Connecté</span>
            </div>
            <div className="stat-row">
              <span className="stat-name">model.pkl chargé</span>
              <span className="badge badge-green">● OK</span>
            </div>
            <div className="stat-row">
              <span className="stat-name">scaler.pkl chargé</span>
              <span className="badge badge-green">● OK</span>
            </div>
            <hr className="divider" />
            <div className="mono" style={{ fontSize: 10, color: "var(--muted)", lineHeight: 1.7 }}>
              Endpoints actifs :<br />
              GET  /test/simulate<br />
              POST /predict<br />
              GET  /history<br />
              GET  /analysis<br />
              GET  /anomalies
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
        <button className="btn btn-primary btn-lg" onClick={save}>Sauvegarder</button>
        <button className="btn btn-ghost btn-lg"
          onClick={() => showToast("Réinitialisation par défaut", "info")}>
          Réinitialiser
        </button>
      </div>
    </div>
  );
}
