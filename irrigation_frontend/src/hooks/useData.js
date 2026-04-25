import { useState, useEffect, useCallback } from "react";
import { getHistory, getAnalysis, getAnomalies, simulate } from "../services/api";

/**
 * useLiveSimulation
 * Appelle GET /test/simulate toutes les `interval` ms
 * pour simuler des données "temps réel" sans vrai capteur.
 *
 * Quand tu brancheras de vrais capteurs :
 *   - soit garde ce hook en mode simulation
 *   - soit remplace simulate() par un appel à ton vrai endpoint capteur
 */
export function useLiveSimulation(interval = 5000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchOnce = useCallback(async () => {
    try {
      const result = await simulate();
      setData(result);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOnce();
    const id = setInterval(fetchOnce, interval);
    return () => clearInterval(id);
  }, [fetchOnce, interval]);

  return { data, loading, error, refresh: fetchOnce };
}

/**
 * useHistory
 * Charge history + analysis + anomalies en parallèle
 */
export function useHistory() {
  const [history, setHistory] = useState([]);
  const [analysis, setAnalysis] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const [h, a, an] = await Promise.all([
        getHistory(),
        getAnalysis(),
        getAnomalies(),
      ]);
      setHistory(h);
      setAnalysis(a);
      setAnomalies(an);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  return { history, analysis, anomalies, loading, error, refresh: fetch };
}

/**
 * usePredict
 * Soumet un payload au POST /predict et retourne le résultat
 */
export function usePredict() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = useCallback(async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const { predict } = await import("../services/api");
      const data = await predict(payload);
      setResult(data);
      return data;
    } catch (e) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { result, loading, error, run };
}
