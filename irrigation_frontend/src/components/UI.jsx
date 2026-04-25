import { useState, useEffect } from "react";

// ─── Toast ────────────────────────────────────────────────────────────────────
let _toastFn = null;
export function showToast(msg, type = "success") {
  if (_toastFn) _toastFn(msg, type);
}

export function Toasts() {
  const [toasts, setToasts] = useState([]);
  useEffect(() => {
    _toastFn = (msg, type) => {
      const id = Date.now();
      setToasts(t => [...t, { id, msg, type }]);
      setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500);
    };
  }, []);
  const icons = { success: "✓", error: "✕", info: "ℹ" };
  return (
    <div className="toast-wrap">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`}>
          <span>{icons[t.type]}</span> {t.msg}
        </div>
      ))}
    </div>
  );
}

// ─── Sparkline SVG ────────────────────────────────────────────────────────────
export function Sparkline({ data, color = "#4ade80", height = 40 }) {
  if (!data || data.length < 2) return null;
  const max = Math.max(...data), min = Math.min(...data);
  const w = 200, h = height;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / (max - min + 0.001)) * (h - 6) - 3;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="sparkline" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ─── Bar chart ────────────────────────────────────────────────────────────────
export function BarChart({ data, accessor, color }) {
  if (!data || data.length === 0) return <div className="loader">Aucune donnée</div>;
  const max = Math.max(...data.map(d => d[accessor])) || 1;
  return (
    <div className="bar-chart">
      {data.map((d, i) => (
        <div key={i} className="bar-col">
          <div className="bar-fill"
            style={{ height: `${(d[accessor] / max) * 100}%`, background: color }} />
          <span className="bar-label">{String(d.date || "").split(" ")[0]}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Loader ───────────────────────────────────────────────────────────────────
export function Loader({ text = "Chargement…" }) {
  return (
    <div className="loader">
      <div className="spinner" /> {text}
    </div>
  );
}

// ─── ErrorBox ─────────────────────────────────────────────────────────────────
export function ErrorBox({ message, onRetry }) {
  return (
    <div className="error-box" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <span>⚠ {message}</span>
      {onRetry && <button className="btn btn-ghost btn-sm" onClick={onRetry}>Réessayer</button>}
    </div>
  );
}

// ─── PumpRing ─────────────────────────────────────────────────────────────────
export function PumpRing({ active, size = 80, emoji }) {
  return (
    <div className={`pump-ring ${active ? "active" : ""}`}
      style={{ width: size, height: size }}>
      <span style={{ fontSize: size * 0.4 }}>{emoji || (active ? "💧" : "⏸")}</span>
    </div>
  );
}

// ─── Toggle ───────────────────────────────────────────────────────────────────
export function Toggle({ value, onChange }) {
  return (
    <button className={`toggle ${value ? "on" : ""}`} onClick={() => onChange(!value)}>
      <span style={{
        position: "absolute", top: 3, left: value ? 25 : 3,
        width: 20, height: 20, borderRadius: "50%",
        background: "white", transition: "left .3s", display: "block"
      }} />
    </button>
  );
}
