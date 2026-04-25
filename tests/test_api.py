"""
Tests des endpoints FastAPI (main.py)
Lancer avec : pytest tests/test_api.py -v
"""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ── Mock du modèle et du scaler avant d'importer main ─────────────────────────
# On ne veut pas avoir besoin des vrais fichiers .pkl pour les tests
mock_model = MagicMock()
mock_model.predict.return_value = np.array([1])
mock_model.feature_importances_ = np.array([0.4, 0.3, 0.15, 0.1, 0.05])

mock_scaler = MagicMock()
mock_scaler.transform.side_effect = lambda x: x   # retourne les données telles quelles

with (
    patch("joblib.load", side_effect=[mock_model, mock_scaler]),
    patch("api.database.init_db"),
):
    import main
    from main import app

client = TestClient(app, raise_server_exceptions=False)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

VALID_PAYLOAD = {
    "soil_moisture":  45.0,
    "temperature":    28.5,
    "humidity":       60.0,
    "rainfall":       5.0,
    "sunlight_hours": 8.0,
}


# ══════════════════════════════════════════════════════════════════════════════
# GET /
# ══════════════════════════════════════════════════════════════════════════════

class TestHome:

    def test_returns_200(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_returns_html(self):
        r = client.get("/")
        assert "text/html" in r.headers["content-type"]

    def test_contains_form(self):
        r = client.get("/")
        assert "predict-form" in r.text

    def test_contains_simulate_button(self):
        r = client.get("/")
        assert "simulate-btn" in r.text


# ══════════════════════════════════════════════════════════════════════════════
# POST /predict
# ══════════════════════════════════════════════════════════════════════════════

class TestPredict:

    def setup_method(self):
        """Réinitialise le mock avant chaque test."""
        mock_model.predict.return_value = np.array([1])

    def test_valid_payload_returns_200(self):
        r = client.post("/predict", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_response_has_required_fields(self):
        r = client.post("/predict", json=VALID_PAYLOAD)
        data = r.json()
        assert "irrigation_needed" in data
        assert "message" in data
        assert "importance" in data

    def test_irrigation_needed_is_int(self):
        r = client.post("/predict", json=VALID_PAYLOAD)
        assert isinstance(r.json()["irrigation_needed"], int)

    def test_irrigation_needed_is_binary(self):
        r = client.post("/predict", json=VALID_PAYLOAD)
        assert r.json()["irrigation_needed"] in (0, 1)

    def test_importance_has_five_keys(self):
        r = client.post("/predict", json=VALID_PAYLOAD)
        assert len(r.json()["importance"]) == 5

    def test_message_when_irrigation_needed(self):
        mock_model.predict.return_value = np.array([1])
        r = client.post("/predict", json=VALID_PAYLOAD)
        assert "irrigation" in r.json()["message"].lower()

    def test_message_when_no_irrigation(self):
        mock_model.predict.return_value = np.array([0])
        r = client.post("/predict", json=VALID_PAYLOAD)
        assert "pas d'irrigation" in r.json()["message"].lower()

    # ── Validation des bornes ──────────────────────────────────────────────

    def test_soil_moisture_below_zero_returns_422(self):
        payload = {**VALID_PAYLOAD, "soil_moisture": -5.0}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_soil_moisture_above_100_returns_422(self):
        payload = {**VALID_PAYLOAD, "soil_moisture": 150.0}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_temperature_above_60_returns_422(self):
        payload = {**VALID_PAYLOAD, "temperature": 70.0}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_sunlight_above_24_returns_422(self):
        payload = {**VALID_PAYLOAD, "sunlight_hours": 25.0}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_missing_field_returns_422(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "rainfall"}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_wrong_type_returns_422(self):
        payload = {**VALID_PAYLOAD, "soil_moisture": "pas_un_nombre"}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    # ── Modèle indisponible ────────────────────────────────────────────────

    def test_model_unavailable_returns_500(self, monkeypatch):
        monkeypatch.setattr(main, "model", None)
        r = client.post("/predict", json=VALID_PAYLOAD)
        assert r.status_code == 500
        assert r.json()["error"] == "model_error"


# ══════════════════════════════════════════════════════════════════════════════
# GET /test/simulate
# ══════════════════════════════════════════════════════════════════════════════

class TestSimulate:

    def test_returns_200(self):
        r = client.get("/test/simulate")
        assert r.status_code == 200

    def test_has_simulated_input(self):
        r = client.get("/test/simulate")
        assert "simulated_input" in r.json()

    def test_simulated_input_has_all_fields(self):
        data = client.get("/test/simulate").json()["simulated_input"]
        for field in ["soil_moisture", "temperature", "humidity", "rainfall", "sunlight_hours"]:
            assert field in data

    def test_soil_moisture_in_valid_range(self):
        data = client.get("/test/simulate").json()["simulated_input"]
        assert 0 <= data["soil_moisture"] <= 100

    def test_different_values_each_call(self):
        """Deux appels successifs ne doivent pas retourner exactement les mêmes données."""
        r1 = client.get("/test/simulate").json()["simulated_input"]
        r2 = client.get("/test/simulate").json()["simulated_input"]
        # Il est astronomiquement improbable que toutes les valeurs soient identiques
        assert r1 != r2

    def test_model_unavailable_returns_500(self, monkeypatch):
        monkeypatch.setattr(main, "model", None)
        r = client.get("/test/simulate")
        assert r.status_code == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /history  /analysis  /anomalies
# ══════════════════════════════════════════════════════════════════════════════

class TestHistoryEndpoints:

    def test_history_returns_200(self):
        with patch("main.get_history_7days", return_value=[]):
            assert client.get("/history").status_code == 200

    def test_analysis_returns_200(self):
        with patch("main.get_daily_aggregates_7days", return_value=[]):
            assert client.get("/analysis").status_code == 200

    def test_anomalies_returns_200(self):
        with patch("main.get_anomalies_7days", return_value=[]):
            assert client.get("/anomalies").status_code == 200

    def test_history_returns_list(self):
        with patch("main.get_history_7days", return_value=[]):
            r = client.get("/history")
            assert isinstance(r.json(), list)

    def test_database_error_returns_503(self):
        from error_handlers import DatabaseError
        with patch("main.get_history_7days", side_effect=DatabaseError("test")):
            r = client.get("/history")
            assert r.status_code == 503
            assert r.json()["error"] == "database_error"