import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

from error_handlers import DatabaseError, logger

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / 'irrigation_history.db'

# ─── Débit configurable ────────────────────────────────────────────────────────
FLOW_RATE_L_PER_MIN: float = 2.0
IRRIGATION_DURATION_MIN: float = 5.0

def _calc_water_used(irrigation_needed: int) -> float:
    if irrigation_needed != 1:
        return 0.0
    return round(FLOW_RATE_L_PER_MIN * IRRIGATION_DURATION_MIN, 2)


# ─── Initialisation ────────────────────────────────────────────────────────────
def init_db() -> None:
    """Crée la table logs si elle n'existe pas. Appelée une seule fois au démarrage."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp         DATETIME DEFAULT CURRENT_TIMESTAMP,
                    soil_moisture     REAL,
                    temperature       REAL,
                    humidity          REAL,
                    rainfall          REAL,
                    sunlight_hours    REAL,
                    irrigation_needed INTEGER,
                    water_used        REAL
                )
            ''')
            conn.commit()
        logger.info("Base de données initialisée avec succès.")
    except sqlite3.Error as e:
        logger.critical(f"Impossible d'initialiser la base de données : {e}")
        raise DatabaseError(f"init_db() a échoué : {e}") from e


# ─── Écriture ──────────────────────────────────────────────────────────────────
def log_prediction(data: Dict[str, float], irrigation_needed: int) -> None:
    """Enregistre une prédiction. Lève DatabaseError si l'écriture échoue."""
    water_used = _calc_water_used(irrigation_needed)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO logs
                    (soil_moisture, temperature, humidity, rainfall,
                     sunlight_hours, irrigation_needed, water_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['soil_moisture'],
                data['temperature'],
                data['humidity'],
                data['rainfall'],
                data['sunlight_hours'],
                irrigation_needed,
                water_used
            ))
            conn.commit()
        logger.info(f"Prédiction enregistrée — irrigation={irrigation_needed}, eau={water_used}L")
    except sqlite3.Error as e:
        logger.error(f"log_prediction() a échoué : {e}")
        raise DatabaseError(f"Impossible d'enregistrer la prédiction : {e}") from e


# ─── Lectures ──────────────────────────────────────────────────────────────────
def get_history_7days() -> List[Dict[str, Any]]:
    """Retourne les logs des 7 derniers jours. Lève DatabaseError si la lecture échoue."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query("""
                SELECT *
                FROM logs
                WHERE timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp DESC
            """, conn)
        logger.info(f"get_history_7days() — {len(df)} lignes retournées")
        return df.to_dict('records')
    except sqlite3.Error as e:
        logger.error(f"get_history_7days() a échoué : {e}")
        raise DatabaseError(f"Lecture de l'historique impossible : {e}") from e


def get_daily_aggregates_7days() -> List[Dict[str, Any]]:
    """Retourne les agrégats journaliers sur 7 jours. Lève DatabaseError si besoin."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query("""
                SELECT
                    date(timestamp)                                         AS date,
                    SUM(water_used)                                         AS total_water,
                    SUM(CASE WHEN irrigation_needed = 1 THEN 1 ELSE 0 END) AS irrigation_count
                FROM logs
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY date(timestamp)
                ORDER BY date DESC
            """, conn)
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        logger.info(f"get_daily_aggregates_7days() — {len(df)} jours")
        return df.to_dict('records')
    except sqlite3.Error as e:
        logger.error(f"get_daily_aggregates_7days() a échoué : {e}")
        raise DatabaseError(f"Agrégats journaliers impossibles : {e}") from e


def get_anomalies_7days() -> List[Dict[str, Any]]:
    """Détecte les valeurs aberrantes de soil_moisture par IQR. Retourne [] si pas de données."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query("""
                SELECT *
                FROM logs
                WHERE timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp DESC
            """, conn)
    except sqlite3.Error as e:
        logger.error(f"get_anomalies_7days() a échoué : {e}")
        raise DatabaseError(f"Lecture des anomalies impossible : {e}") from e

    if df.empty:
        logger.info("get_anomalies_7days() — aucune donnée disponible")
        return []

    Q1 = df['soil_moisture'].quantile(0.25)
    Q3 = df['soil_moisture'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    anomalies = df[
        (df['soil_moisture'] < lower) | (df['soil_moisture'] > upper)
    ].to_dict('records')

    logger.info(f"get_anomalies_7days() — {len(anomalies)} anomalie(s) détectée(s)")
    return anomalies