import sqlite3
import json
import base64
from pathlib import Path

# --- Paths ---
DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "trades.db"
DATA_DIR.mkdir(exist_ok=True)

# --- Initialize Database ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT,
            session TEXT,
            date TEXT,
            entry_time TEXT,
            exit_time TEXT,
            trade_type TEXT,
            planned_rr REAL,
            realized_rr REAL,
            profit_percent REAL,
            risk_per_trade REAL,
            notes TEXT,
            rights_wrongs TEXT,
            screenshots TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- Add a Trade ---
def add_trade(trade_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades (
            pair, session, date, entry_time, exit_time, trade_type,
            planned_rr, realized_rr, profit_percent, risk_per_trade,
            notes, rights_wrongs, screenshots
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_data.get("pair"),
        trade_data.get("session"),
        trade_data.get("date"),
        trade_data.get("entry_time"),
        trade_data.get("exit_time"),
        trade_data.get("trade_type"),
        trade_data.get("planned_rr"),
        trade_data.get("realized_rr"),
        trade_data.get("profit_percent"),
        trade_data.get("risk_per_trade"),
        trade_data.get("notes"),
        trade_data.get("rights_wrongs"),
        json.dumps(trade_data.get("screenshots", {}))  # base64 strings
    ))
    conn.commit()
    conn.close()

# --- Fetch All Trades ---
def fetch_all_trades():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades ORDER BY date DESC")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    trades = [dict(zip(columns, row)) for row in rows]
    return trades

# --- Update Trade ---
def update_trade(trade_id: int, trade_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE trades
        SET pair=?, session=?, date=?, entry_time=?, exit_time=?, trade_type=?,
            planned_rr=?, realized_rr=?, profit_percent=?, risk_per_trade=?,
            notes=?, rights_wrongs=?, screenshots=?
        WHERE id=?
    """, (
        trade_data.get("pair"),
        trade_data.get("session"),
        trade_data.get("date"),
        trade_data.get("entry_time"),
        trade_data.get("exit_time"),
        trade_data.get("trade_type"),
        trade_data.get("planned_rr"),
        trade_data.get("realized_rr"),
        trade_data.get("profit_percent"),
        trade_data.get("risk_per_trade"),
        trade_data.get("notes"),
        trade_data.get("rights_wrongs"),
        json.dumps(trade_data.get("screenshots", {})),
        trade_id
    ))
    conn.commit()
    conn.close()
