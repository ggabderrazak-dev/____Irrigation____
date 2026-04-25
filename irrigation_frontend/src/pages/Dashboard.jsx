import { useLiveSimulation } from "../hooks/useData";
import { Sparkline, Loader, ErrorBox, PumpRing } from "../components/UI";

export default function PageDashboard() {
  const { data, loading, error, refresh } = useLiveSimulation(5000);

  if (loading) return <Loader text="Connexion à l'API…" />;
  if (error)   return <ErrorBox message={error} onRetry={refresh} />;

  // data.simulated_input vient de GET /test/simulate → main.py
  const s = data.simulated_input;
  const pumpActive = data.irrigation_needed === 1;

  const metrics = [
    { label: "Humidité sol",  value: s.soil_moisture.toFixed(1),  unit: "%",   color: "#4ade80" },
    { label: "Température",   value: s.temperature.toFixed(1),    unit: "°C",  color: "#fbbf24" },
    { label: "Humidité air",  value: s.humidity.toFixed(0),       unit: "%",   color: "#60a5fa" },
    { label: "Pluie",         value: s.rainfall.toFixed(1),       unit: "mm",  color: "#a78bfa" },
  ];

  // importance vient du modèle RandomForest de main.py
  const imp = data.importance || {};
  const impEntries = Object.entries(imp).sort((a, b) => b[1] - a[1]);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle mono">
          Données temps réel · Rafraîchi toutes les 5s via <code>/test/simulate</code>
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        {metrics.map((m, i) => (
          <div key={i} className="card card-glow">
            <div className="metric-label">{m.label}</div>
            <div className="metric-value" style={{ color: m.color }}>
              {m.value}<span className="metric-unit">{m.unit}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid-2-1">
        {/* Importance features */}
        <div className="card card-glow">
          <div className="section-title">
            Importance des facteurs (modèle IA)
            <div className="section-line" />
          </div>
          <p className="mono" style={{ fontSize: 11, color: "var(--muted)", marginBottom: 16 }}>
            Source : <code>model.feature_importances_</code> — RandomForest
          </p>
          {impEntries.map(([key, val]) => (
            <div key={key} style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 12, fontWeight: 600 }}>{key}</span>
                <span className="mono" style={{ fontSize: 12, color: "var(--muted)" }}>
                  {(val * 100).toFixed(1)}%
                </span>
              </div>
              <div className="progress-track">
                <div className="progress-fill"
                  style={{ width: `${val * 100}%`, background: "var(--accent)" }} />
              </div>
            </div>
          ))}
        </div>

        {/* Pump status */}
        <div className="card card-glow">
          <div className="section-title">État pompe <div className="section-line" /></div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, paddingTop: 8 }}>
            <PumpRing active={pumpActive} size={90} />
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>
                {pumpActive ? "Irrigation recommandée" : "Pas d'irrigation"}
              </div>
              <div className="mono" style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>
                Prédiction IA · <code>/test/simulate</code>
              </div>
            </div>
            <span className={`badge ${pumpActive ? "badge-green" : "badge-yellow"}`}>
              {pumpActive ? "● IRRIGUER" : "○ SUFFISANT"}
            </span>
          </div>

          <hr className="divider" />
          <div className="stat-row">
            <span className="stat-name">Résultat modèle</span>
            <span className="stat-val mono">{data.irrigation_needed}</span>
          </div>
          <div className="stat-row">
            <span className="stat-name">Débit configuré</span>
            <span className="stat-val mono">2.0 L/min</span>
          </div>
          <div className="stat-row">
            <span className="stat-name">Durée cycle</span>
            <span className="stat-val mono">5 min</span>
          </div>
        </div>
      </div>

      {/* IA message */}
      <div style={{ marginTop: 16 }}>
        <div className="card" style={{
          borderColor: pumpActive ? "rgba(74,222,128,.3)" : "rgba(251,191,36,.3)",
          background: pumpActive ? "rgba(74,222,128,.04)" : "rgba(251,191,36,.04)"
        }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>
            💬 {data.message}
          </span>
        </div>
      </div>
    </div>
  );
}
