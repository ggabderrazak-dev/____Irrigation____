import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / 'irrigation_history.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            soil_moisture REAL,
            temperature REAL,
            humidity REAL,
            rainfall REAL,
            sunlight_hours REAL,
            irrigation_needed INTEGER,
            water_used REAL
        )
    ''')
    conn.commit()
    conn.close()

def log_prediction(data: Dict[str, float], irrigation_needed: int):
    init_db()  # Ensure table exists
    water_used = 10.0 if irrigation_needed == 1 else 0.0
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (soil_moisture, temperature, humidity, rainfall, sunlight_hours, irrigation_needed, water_used)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['soil_moisture'], data['temperature'], data['humidity'], data['rainfall'], data['sunlight_hours'], irrigation_needed, water_used))
    conn.commit()
    conn.close()

def get_history_7days() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT * FROM logs 
        WHERE timestamp >= datetime('now', '-7 days')
        ORDER BY timestamp DESC
    """, conn)
    conn.close()
    return df.to_dict('records')

def get_daily_aggregates_7days() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT 
            date(timestamp) as date,
            SUM(water_used) as total_water,
            SUM(CASE WHEN irrigation_needed = 1 THEN 1 ELSE 0 END) as irrigation_count
        FROM logs 
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY date(timestamp)
        ORDER BY date DESC
    """, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    return df.to_dict('records')

def get_anomalies_7days() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT * FROM logs 
        WHERE timestamp >= datetime('now', '-7 days')
        ORDER BY timestamp DESC
    """, conn)
    conn.close()
    if len(df) == 0:
        return []
    # IQR outlier on soil_moisture (broken sensor proxy)
    Q1 = df['soil_moisture'].quantile(0.25)
    Q3 = df['soil_moisture'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    anomalies = df[(df['soil_moisture'] < lower) | (df['soil_moisture'] > upper)].to_dict('records')
    return anomalies
