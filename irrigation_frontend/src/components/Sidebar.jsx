// Sidebar.jsx
export default function Sidebar({ active, setActive, apiOnline }) {
  const NAV = [
    { id: "dashboard", icon: "◈", label: "Dashboard" },
    { id: "control",   icon: "⊡", label: "Contrôle"  },
    { id: "schedule",  icon: "◷", label: "Planning"  },
    { id: "history",   icon: "◫", label: "Historique" },
    { id: "settings",  icon: "◎", label: "Paramètres" },
  ];

  return (
    <div className="sidebar">
      <div className="logo">
        <div className="logo-icon">🌿</div>
        <div>
          <div className="logo-text">IrrigAI</div>
          <div className="logo-sub">v2.0</div>
        </div>
      </div>

      <div className="nav-section">Navigation</div>
      {NAV.map(n => (
        <div key={n.id}
          className={`nav-item ${active === n.id ? "active" : ""}`}
          onClick={() => setActive(n.id)}
        >
          <span className="nav-icon">{n.icon}</span>
          <span>{n.label}</span>
        </div>
      ))}

      <div className="sidebar-footer">
        <span className={`status-dot ${apiOnline ? "" : "offline"}`} />
        <span className="status-text">
          {apiOnline ? "API connectée" : "API hors ligne"}
        </span>
      </div>
    </div>
  );
}
