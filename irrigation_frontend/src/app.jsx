import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import { Toasts } from "./components/UI";
import PageDashboard from "./pages/Dashboard";
import PageControl   from "./pages/Control";
import PageSchedule  from "./pages/Schedule";
import PageHistory   from "./pages/History";
import PageSettings  from "./pages/Settings";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    fetch(`${BASE_URL}/history`, {
      headers: API_KEY ? { "X-API-Key": API_KEY } : {},
    })
      .then(r => setApiOnline(r.ok))
      .catch(() => setApiOnline(false));
  }, []);

  const pages = {
    dashboard: <PageDashboard />,
    control:   <PageControl />,
    schedule:  <PageSchedule />,
    history:   <PageHistory />,
    settings:  <PageSettings />,
  };

  return (
    <>
      <Toasts />
      <div className="layout">
        <Sidebar active={page} setActive={setPage} apiOnline={apiOnline} />
        <div className="main">
          {pages[page]}
        </div>
      </div>
    </>
  );
}
