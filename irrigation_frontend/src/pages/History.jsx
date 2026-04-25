import { useHistory } from "../hooks/useData";
import { BarChart, Sparkline, Loader, ErrorBox } from "../components/UI";
import { useState } from "react";

export default function PageHistory() {
  const { history, analysis, anomalies, loading, error, refresh } = useHistory();
  const [filter, setFilter] = useState("all");

  if (loading) return <Loader text="Chargement historique…" />;
  if (error)   return <ErrorBox message={error} onRetry={refresh} />;

  const filtered = filter === "all"
    ? history
    : history.filter(r => r.irrigation_needed === 1);

  const moistureData = history.map(r => r.soil_moisture).filter(Boolean);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Historique</h1>
        <p className="page-subtitle mono">
          Données des 7 derniers jours · <code>/history</code> <code>/analysis</code> <code>/anomalies</code>
        </p>
      </div>

      {/* Anomaly alert */}
      {anomalies.length > 0 && (
        <div style={{
          background: "rgba(248,113,113,.08)", border: "1px solid rgba(248,113,113,.3)",
          borderRadius: 10, padding: "14px 18px", marginBottom: 20,
          display: "flex", alignItems: "center", gap: 12
        }}>
          <span style={{ fontSize: 20 }}>⚠</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--danger)" }}>
              {anomalies.length} anomalie(s) détectée(s) sur l'humidité sol
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>
              Source : <code>GET /anomalies</code> — détection IQR dans database.py
            </div>
          </div>
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Sparkline */}
        <div className="card card-glow">
          <div className="section-title">Humidité sol — tendance 7j <div className="section-line" /></div>
          {moistureData.length > 1 ? (
            <Sparkline data={moistureData} color="var(--accent)" height={60} />
          ) : <div style={{ color: "var(--muted)", fontSize: 12 }}>Données insuffisantes</div>}
        </div>

        {/* Aggregates bar chart */}
        <div className="card card-glow">
          <div className="section-title">Eau consommée/jour <div className="section-line" /></div>
          {analysis.length > 0 ? (
            <BarChart data={analysis} accessor="total_water" color="var(--info)" />
          ) : <div style={{ color: "var(--muted)", fontSize: 12 }}>Aucun agrégat disponible</div>}
        </div>
      </div>

      {/* Main table */}
      <div className="card card-glow">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div className="section-title" style={{ margin: 0 }}>
            Logs bruts <code style={{ fontSize: 11, fontWeight: 400 }}>GET /history</code>
            <div className="section-line" />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className={`btn btn-sm ${filter === "all" ? "btn-primary" : "btn-ghost"}`} onClick={() => setFilter("all")}>
              Tout ({history.length})
            </button>
            <button className={`btn btn-sm ${filter === "irr" ? "btn-primary" : "btn-ghost"}`} onClick={() => setFilter("irr")}>
              Irrigations
            </button>
          </div>
        </div>

        {filtered.length === 0 ? (
          <div style={{ color: "var(--muted)", fontSize: 13, padding: "20px 0" }}>
            Aucune donnée disponible. Lance une prédiction depuis Contrôle.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Horodatage</th>
                  <th>Sol %</th>
                  <th>Temp °C</th>
                  <th>Humidité %</th>
                  <th>Pluie mm</th>
                  <th>Soleil h</th>
                  <th>Eau L</th>
                  <th>Irrigation</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => (
                  <tr key={i}>
                    <td className="mono" style={{ color: "var(--muted)", fontSize: 11 }}>
                      {new Date(r.timestamp).toLocaleString("fr-FR")}
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div className="progress-track" style={{ width: 50 }}>
                          <div className="progress-fill" style={{
                            width: `${r.soil_moisture}%`,
                            background: r.soil_moisture < 40 ? "var(--danger)" : "var(--accent)"
                          }} />
                        </div>
                        <span className="mono" style={{ fontSize: 11 }}>{r.soil_moisture?.toFixed(1)}</span>
                      </div>
                    </td>
                    <td className="mono">{r.temperature?.toFixed(1)}</td>
                    <td className="mono">{r.humidity?.toFixed(1)}</td>
                    <td className="mono">{r.rainfall?.toFixed(1)}</td>
                    <td className="mono">{r.sunlight_hours?.toFixed(1)}</td>
                    <td className="mono" style={{ color: "var(--info)" }}>{r.water_used}</td>
                    <td>
                      <span className={`badge ${r.irrigation_needed === 1 ? "badge-green" : "badge-yellow"}`}>
                        {r.irrigation_needed === 1 ? "Oui" : "Non"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Daily aggregates */}
      {analysis.length > 0 && (
        <div className="card card-glow" style={{ marginTop: 16 }}>
          <div className="section-title">
            Agrégats journaliers <code style={{ fontSize: 11, fontWeight: 400 }}>GET /analysis</code>
            <div className="section-line" />
          </div>
          <table className="table">
            <thead>
              <tr><th>Date</th><th>Eau totale (L)</th><th>Nb irrigations</th></tr>
            </thead>
            <tbody>
              {analysis.map((a, i) => (
                <tr key={i}>
                  <td className="mono">{a.date}</td>
                  <td className="mono" style={{ color: "var(--info)" }}>{a.total_water?.toFixed(2)}</td>
                  <td className="mono">{a.irrigation_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
