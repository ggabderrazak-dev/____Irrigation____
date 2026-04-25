import { useState } from "react";
import { showToast, Toggle } from "../components/UI";

const INITIAL_SCHEDULES = [
  { id: 1, time: "06:00", name: "Aube – Zone A",         days: "Lun Mer Ven", duration: 5,  active: true  },
  { id: 2, time: "12:30", name: "Midi – Zone B",         days: "Mar Jeu",     duration: 3,  active: true  },
  { id: 3, time: "19:00", name: "Soir – Toutes zones",   days: "Quotidien",   duration: 8,  active: false },
];

export default function PageSchedule() {
  const [schedules, setSchedules] = useState(INITIAL_SCHEDULES);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ time: "", name: "", days: "Quotidien", duration: 5 });

  const add = () => {
    if (!form.time || !form.name) { showToast("Remplis tous les champs", "error"); return; }
    setSchedules(s => [...s, { ...form, id: Date.now(), active: true }]);
    setForm({ time: "", name: "", days: "Quotidien", duration: 5 });
    setShowForm(false);
    showToast("Programme ajouté", "success");
  };

  const toggle = (id) => {
    setSchedules(s => s.map(x => x.id === id ? { ...x, active: !x.active } : x));
    showToast("Planning mis à jour", "info");
  };

  const remove = (id) => {
    setSchedules(s => s.filter(x => x.id !== id));
    showToast("Programme supprimé", "error");
  };

  const active = schedules.filter(s => s.active);
  const nextCycle = [...active].sort((a, b) => a.time.localeCompare(b.time))[0];
  const estimatedWater = active.reduce((sum, s) => sum + s.duration * 2, 0);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Planification</h1>
        <p className="page-subtitle mono">
          Programmation des cycles · Stockage local (ajoute un endpoint <code>/schedules</code> pour persister)
        </p>
      </div>

      <div className="grid-2-1">
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <span style={{ fontSize: 14, fontWeight: 700 }}>
              Programmes ({active.length}/{schedules.length} actifs)
            </span>
            <button className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
              + Nouveau
            </button>
          </div>

          {schedules.map(s => (
            <div key={s.id} className="schedule-item" style={{ opacity: s.active ? 1 : 0.5 }}>
              <div className="schedule-time">{s.time}</div>
              <div className="schedule-info">
                <div className="schedule-name">{s.name}</div>
                <div className="schedule-meta">{s.days} · {s.duration} min · {s.duration * 2} L estimés</div>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <Toggle value={s.active} onChange={() => toggle(s.id)} />
                <button className="btn btn-ghost btn-sm" onClick={() => remove(s.id)}>✕</button>
              </div>
            </div>
          ))}

          {schedules.length === 0 && (
            <div style={{ color: "var(--muted)", fontSize: 13, padding: "20px 0" }}>
              Aucun programme. Clique "+ Nouveau" pour en créer un.
            </div>
          )}

          {showForm && (
            <div className="card" style={{ marginTop: 16, border: "1px solid rgba(74,222,128,.3)" }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: "var(--accent)" }}>
                Nouveau programme
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Heure</label>
                  <input type="time" className="form-input"
                    value={form.time} onChange={e => setForm(f => ({ ...f, time: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Durée (min)</label>
                  <input type="number" className="form-input"
                    value={form.duration} min={1} max={60}
                    onChange={e => setForm(f => ({ ...f, duration: parseInt(e.target.value) }))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Nom</label>
                <input type="text" className="form-input" placeholder="ex : Matin – Zone A"
                  value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Jours</label>
                <select className="form-input form-select"
                  value={form.days} onChange={e => setForm(f => ({ ...f, days: e.target.value }))}>
                  <option>Quotidien</option>
                  <option>Lun Mer Ven</option>
                  <option>Mar Jeu Sam</option>
                  <option>Week-end</option>
                </select>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button className="btn btn-primary" onClick={add}>Ajouter</button>
                <button className="btn btn-ghost" onClick={() => setShowForm(false)}>Annuler</button>
              </div>
            </div>
          )}
        </div>

        {/* Summary */}
        <div className="card card-glow">
          <div className="section-title">Résumé <div className="section-line" /></div>
          <div className="stat-row">
            <span className="stat-name">Programmes total</span>
            <span className="stat-val">{schedules.length}</span>
          </div>
          <div className="stat-row">
            <span className="stat-name">Actifs</span>
            <span className="stat-val" style={{ color: "var(--accent)" }}>{active.length}</span>
          </div>
          <div className="stat-row">
            <span className="stat-name">Prochain cycle</span>
            <span className="stat-val mono" style={{ color: "var(--accent)" }}>
              {nextCycle?.time || "—"}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-name">Eau estimée/j</span>
            <span className="stat-val mono">~{estimatedWater} L</span>
          </div>

          <hr className="divider" />
          <div style={{ fontSize: 11, color: "var(--muted)", fontFamily: "'DM Mono', monospace", lineHeight: 1.6 }}>
            💡 Pour persister les programmes, ajoute un endpoint <code>POST /schedules</code> dans main.py
            et une table <code>schedules</code> dans database.py.
          </div>
        </div>
      </div>
    </div>
  );
}
