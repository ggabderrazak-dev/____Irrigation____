"""
Tests unitaires pour database.py
Lancer avec : pytest tests/test_database.py -v
"""
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# ── On redirige la DB vers une base de test en mémoire ────────────────────────
import database
database.DB_PATH = Path(":memory:")   # n'écrit rien sur le disque

from database import (
    init_db, log_prediction, get_history_7days,
    get_daily_aggregates_7days, get_anomalies_7days,
    _calc_water_used, FLOW_RATE_L_PER_MIN, IRRIGATION_DURATION_MIN
)
from error_handlers import DatabaseError


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """
    Avant chaque test : crée une base SQLite temporaire sur disque (tmp_path).
    ":memory:" ne fonctionne pas bien avec pandas.read_sql_query sur des
    connexions séparées, donc on utilise un fichier temporaire.
    """
    db_file = tmp_path / "test_irrigation.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    init_db()
    yield


SAMPLE_DATA = {
    "soil_moisture":  45.0,
    "temperature":    28.5,
    "humidity":       60.0,
    "rainfall":       5.0,
    "sunlight_hours": 8.0,
}


# ══════════════════════════════════════════════════════════════════════════════
# Tests de _calc_water_used
# ══════════════════════════════════════════════════════════════════════════════

class TestCalcWaterUsed:

    def test_irrigation_needed_returns_positive(self):
        result = _calc_water_used(1)
        assert result > 0

    def test_no_irrigation_returns_zero(self):
        assert _calc_water_used(0) == 0.0

    def test_value_matches_config(self):
        expected = round(FLOW_RATE_L_PER_MIN * IRRIGATION_DURATION_MIN, 2)
        assert _calc_water_used(1) == expected

    def test_return_type_is_float(self):
        assert isinstance(_calc_water_used(1), float)
        assert isinstance(_calc_water_used(0), float)


# ══════════════════════════════════════════════════════════════════════════════
# Tests de init_db
# ══════════════════════════════════════════════════════════════════════════════

class TestInitDb:

    def test_table_exists_after_init(self, tmp_path, monkeypatch):
        db_file = tmp_path / "fresh.db"
        monkeypatch.setattr(database, "DB_PATH", db_file)
        init_db()
        with sqlite3.connect(db_file) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        assert ("logs",) in tables

    def test_init_is_idempotent(self):
        """Appeler init_db() deux fois ne doit pas lever d'erreur."""
        init_db()
        init_db()

    def test_raises_database_error_on_bad_path(self, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", Path("/chemin/inexistant/db.sqlite"))
        with pytest.raises(DatabaseError):
            init_db()


# ══════════════════════════════════════════════════════════════════════════════
# Tests de log_prediction
# ══════════════════════════════════════════════════════════════════════════════

class TestLogPrediction:

    def test_inserts_one_row(self):
        log_prediction(SAMPLE_DATA, irrigation_needed=1)
        rows = get_history_7days()
        assert len(rows) == 1

    def test_values_are_stored_correctly(self):
        log_prediction(SAMPLE_DATA, irrigation_needed=1)
        row = get_history_7days()[0]
        assert row["soil_moisture"]  == SAMPLE_DATA["soil_moisture"]
        assert row["temperature"]    == SAMPLE_DATA["temperature"]
        assert row["irrigation_needed"] == 1

    def test_water_used_zero_when_no_irrigation(self):
        log_prediction(SAMPLE_DATA, irrigation_needed=0)
        row = get_history_7days()[0]
        assert row["water_used"] == 0.0

    def test_water_used_positive_when_irrigation(self):
        log_prediction(SAMPLE_DATA, irrigation_needed=1)
        row = get_history_7days()[0]
        assert row["water_used"] > 0

    def test_multiple_rows(self):
        for i in range(5):
            log_prediction(SAMPLE_DATA, irrigation_needed=i % 2)
        rows = get_history_7days()
        assert len(rows) == 5

    def test_raises_database_error_on_bad_path(self, monkeypatch):
        monkeypatch.setattr(database, "DB_PATH", Path("/chemin/inexistant/db.sqlite"))
        with pytest.raises(DatabaseError):
            log_prediction(SAMPLE_DATA, 1)


# ══════════════════════════════════════════════════════════════════════════════
# Tests de get_history_7days
# ══════════════════════════════════════════════════════════════════════════════

class TestGetHistory7Days:

    def test_empty_db_returns_empty_list(self):
        assert get_history_7days() == []

    def test_returns_list_of_dicts(self):
        log_prediction(SAMPLE_DATA, 1)
        result = get_history_7days()
        assert isinstance(result, list)
        assert isinstance(result[0], dict)

    def test_expected_columns_present(self):
        log_prediction(SAMPLE_DATA, 1)
        row = get_history_7days()[0]
        for col in ["id", "timestamp", "soil_moisture", "temperature",
                    "humidity", "rainfall", "sunlight_hours",
                    "irrigation_needed", "water_used"]:
            assert col in row, f"Colonne manquante : {col}"

    def test_ordered_most_recent_first(self):
        for _ in range(3):
            log_prediction(SAMPLE_DATA, 1)
        rows = get_history_7days()
        timestamps = [r["timestamp"] for r in rows]
        assert timestamps == sorted(timestamps, reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
# Tests de get_daily_aggregates_7days
# ══════════════════════════════════════════════════════════════════════════════

class TestGetDailyAggregates:

    def test_empty_db_returns_empty_list(self):
        assert get_daily_aggregates_7days() == []

    def test_aggregates_irrigation_count(self):
        # 3 irrigations aujourd'hui
        for _ in range(3):
            log_prediction(SAMPLE_DATA, irrigation_needed=1)
        # 1 non-irrigation
        log_prediction(SAMPLE_DATA, irrigation_needed=0)

        result = get_daily_aggregates_7days()
        assert len(result) == 1  # tout le même jour
        assert result[0]["irrigation_count"] == 3

    def test_total_water_calculation(self):
        expected_per_cycle = round(FLOW_RATE_L_PER_MIN * IRRIGATION_DURATION_MIN, 2)
        for _ in range(4):
            log_prediction(SAMPLE_DATA, irrigation_needed=1)

        result = get_daily_aggregates_7days()
        assert abs(result[0]["total_water"] - expected_per_cycle * 4) < 0.01

    def test_date_format_is_iso(self):
        log_prediction(SAMPLE_DATA, 1)
        result = get_daily_aggregates_7days()
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}", result[0]["date"])


# ══════════════════════════════════════════════════════════════════════════════
# Tests de get_anomalies_7days
# ══════════════════════════════════════════════════════════════════════════════

class TestGetAnomalies:

    def test_empty_db_returns_empty_list(self):
        assert get_anomalies_7days() == []

    def test_no_anomaly_in_uniform_data(self):
        # Toutes les valeurs identiques → pas d'outlier IQR
        for _ in range(10):
            log_prediction(SAMPLE_DATA, 1)
        assert get_anomalies_7days() == []

    def test_detects_extreme_low_moisture(self):
        # 10 valeurs normales + 1 valeur extrêmement basse
        for _ in range(10):
            log_prediction(SAMPLE_DATA, 1)

        outlier = {**SAMPLE_DATA, "soil_moisture": 0.1}
        log_prediction(outlier, 1)

        anomalies = get_anomalies_7days()
        assert len(anomalies) >= 1
        assert any(a["soil_moisture"] == pytest.approx(0.1) for a in anomalies)

    def test_detects_extreme_high_moisture(self):
        for _ in range(10):
            log_prediction(SAMPLE_DATA, 1)

        outlier = {**SAMPLE_DATA, "soil_moisture": 99.9}
        log_prediction(outlier, 1)

        anomalies = get_anomalies_7days()
        assert len(anomalies) >= 1