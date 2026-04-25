import { useState } from "react";
import { usePredict } from "../hooks/useData";
import { PumpRing, Toggle } from "../components/UI";
import { showToast } from "../components/UI";

const MODES = [
  { id: "auto",     icon: "🤖", name: "Automatique", desc: "IA décide" },
  { id: "manual",   icon: "🕹️", name: "Manuel",      desc: "Contrôle total" },
  { id: "schedule", icon: "🗓️", name: "Programmé",   desc: "Horaires fixés" },
];

const INITIAL_FORM = {
  soil_moisture: 45,
  temperature: 28,
  humidity: 60,
  rainfall: 5,
  sunlight_hours: 8,
};

export default function PageControl() {
  const [mode, setMode] = useState("manual");
  const [form, setForm] = useState(INITIAL_FORM);
  const [zones, setZones] = useState({ a: true, b: false, c: false });
  const { result, loading, error, run } = usePredict();

  const handlePredict = async () => {
    // Appelle POST /predict avec les valeurs du formulaire → main.py
    const res = await run(form);
    if (res) showToast(
      res.irrigation_needed === 1 ? "Irrigation recommandée 💧" : "Sol suffisant 🌱",
      res.irrigation_needed === 1 ? "info" : "success"
    );
  };

  const toggleZone = (z) => {
    setZones(prev => ({ ...prev, [z]: !prev[z] }));
    showToast(`Zone ${z.toUpperCase()} ${zones[z] ? "désactivée" : "activée"}`, "info");
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Contrôle</h1>
        <p className="page-subtitle mono">
          Prédiction manuelle via <code>POST /predict</code>
        </p>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Mode selector */}
        <div className="card card-glow">
          <div className="section-title">Mode de fonctionnement <div className="section-line" /></div>
          <div className="mode-grid">
            {MODES.map(m => (
              <div key={m.id}
                className={`mode-card ${mode === m.id ? "selected" : ""}`}
                onClick={() => { setMode(m.id); showToast(`Mode ${m.name} activé`, "success"); }}
              >
                <div className="mode-icon">{m.icon}</div>
                <div className="mode-name">{m.name}</div>
                <div className="mode-desc">{m.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Predict result */}
        <div className="card card-glow">
          <div className="section-title">Résultat IA <div className="section-line" /></div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, paddingTop: 8 }}>
            <PumpRing
              active={result?.irrigation_needed === 1}
              size={90}
              emoji={result ? (result.irrigation_needed === 1 ? "💧" : "🌱") : "?"}
            />
            {result ? (
              <>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 13, fontWeight: 700 }}>{result.message}</div>
                </div>
                <span className={`badge ${result.irrigation_needed === 1 ? "badge-green" : "badge-yellow"}`}>
                  {result.irrigation_needed === 1 ? "● IRRIGUER" : "○ SUFFISANT"}
                </span>
              </>
            ) : (
              <span style={{ fontSize: 12, color: "var(--muted)" }}>
                Remplis le formulaire et clique Prédire
              </span>
            )}
          </div>
          {error && (
            <div className="error-box" style={{ marginTop: 12 }}>⚠ {error}</div>
          )}
        </div>
      </div>

      {/* Manual form → POST /predict */}
      <div className="card card-glow" style={{ marginBottom: 20 }}>
        <div className="section-title">
          Saisie manuelle — <code style={{ fontSize: 12, fontWeight: 400 }}>POST /predict</code>
          <div className="section-line" />
        </div>
        <p className="mono" style={{ fontSize: 11, color: "var(--muted)", marginBottom: 20 }}>
          Correspond exactement à <strong>PredictRequest</strong> dans main.py.
          Validations : soil_moisture 0–100, temperature −20 à 60, humidity 0–100, rainfall 0–500, sunlight_hours 0–24.
        </p>

        <div className="grid-3">
          {[
            { key: "soil_moisture",  label: "Humidité sol (%)",   min: 0,   max: 100, step: 1 },
            { key: "temperature",    label: "Température (°C)",    min: -20, max: 60,  step: 0.1 },
            { key: "humidity",       label: "Humidité air (%)",    min: 0,   max: 100, step: 1 },
            { key: "rainfall",       label: "Pluie (mm)",          min: 0,   max: 500, step: 0.1 },
            { key: "sunlight_hours", label: "Heures de soleil",    min: 0,   max: 24,  step: 0.1 },
          ].map(f => (
            <div key={f.key} className="form-group">
              <label className="form-label">{f.label}</label>
              <input
                type="number"
                className="form-input"
                value={form[f.key]}
                min={f.min} max={f.max} step={f.step}
                onChange={e => setForm(p => ({ ...p, [f.key]: parseFloat(e.target.value) }))}
              />
            </div>
          ))}
        </div>

        <button
          className="btn btn-primary btn-lg"
          onClick={handlePredict}
          disabled={loading}
        >
          {loading ? "⏳ Prédiction…" : "▶ Prédire"}
        </button>
      </div>

      {/* Zones */}
      <div className="card card-glow">
        <div className="section-title">Zones d'irrigation <div className="section-line" /></div>
        <div className="grid-3">
          {[
            { key: "a", name: "Zone A – Pelouse", icon: "🌿" },
            { key: "b", name: "Zone B – Potager", icon: "🥕" },
            { key: "c", name: "Zone C – Arbres",  icon: "🌳" },
          ].map(z => (
            <div key={z.key} className="card card-sm"
              style={{ border: `1px solid ${zones[z.key] ? "rgba(74,222,128,.4)" : "var(--border)"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 22, marginBottom: 4 }}>{z.icon}</div>
                  <div style={{ fontSize: 12, fontWeight: 700 }}>{z.name}</div>
                </div>
                <Toggle value={zones[z.key]} onChange={() => toggleZone(z.key)} />
              </div>
              <span className={`badge ${zones[z.key] ? "badge-green" : "badge-yellow"}`}>
                {zones[z.key] ? "Active" : "Inactive"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
