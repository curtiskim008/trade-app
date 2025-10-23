import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "data/trades.db"

def init_db():
    """Initialize the database and create table if it doesn’t exist."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            pair TEXT,
            session TEXT,
            entry_time TEXT,
            exit_time TEXT,
            trade_type TEXT,
            planned_rr TEXT,
            realized_rr TEXT,
            profit_percent TEXT,
            risk_per_trade TEXT,
            notes TEXT,
            rights_wrongs TEXT,
            screenshots TEXT
        )
    """)
    conn.commit()
    conn.close()

def fetch_all_trades():
    """Fetch all trades from database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM trades ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()

    columns = [
        "id", "date", "pair", "session", "entry_time", "exit_time",
        "trade_type", "planned_rr", "realized_rr", "profit_percent",
        "risk_per_trade", "notes", "rights_wrongs", "screenshots"
    ]

    trades = []
    for row in rows:
        trade = dict(zip(columns, row))

        # Handle screenshots JSON or None
        try:
            if trade["screenshots"]:
                screenshots = json.loads(trade["screenshots"])
                if not isinstance(screenshots, dict):
                    screenshots = {}
            else:
                screenshots = {}
        except Exception:
            screenshots = {}

        trade["screenshots"] = screenshots
        trades.append(trade)

    return trades

def insert_trade(trade_data):
    """Insert a new trade into the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure screenshots are JSON-encoded safely
    screenshots_json = json.dumps(trade_data.get("screenshots", {}))

    c.execute("""
        INSERT INTO trades (
            date, pair, session, entry_time, exit_time, trade_type,
            planned_rr, realized_rr, profit_percent, risk_per_trade,
            notes, rights_wrongs, screenshots
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_data.get("date"),
        trade_data.get("pair"),
        trade_data.get("session"),
        trade_data.get("entry_time"),
        trade_data.get("exit_time"),
        trade_data.get("trade_type"),
        trade_data.get("planned_rr"),
        trade_data.get("realized_rr"),
        trade_data.get("profit_percent"),
        trade_data.get("risk_per_trade"),
        trade_data.get("notes"),
        trade_data.get("rights_wrongs"),
        screenshots_json
    ))

    conn.commit()
    conn.close()

def update_trade(trade_id, updated_data):
    """Update a trade by ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    screenshots_json = json.dumps(updated_data.get("screenshots", {}))

    c.execute("""
        UPDATE trades SET
            date = ?,
            pair = ?,
            session = ?,
            entry_time = ?,
            exit_time = ?,
            trade_type = ?,
            planned_rr = ?,
            realized_rr = ?,
            profit_percent = ?,
            risk_per_trade = ?,
            notes = ?,
            rights_wrongs = ?,
            screenshots = ?
        WHERE id = ?
    """, (
        updated_data.get("date"),
        updated_data.get("pair"),
        updated_data.get("session"),
        updated_data.get("entry_time"),
        updated_data.get("exit_time"),
        updated_data.get("trade_type"),
        updated_data.get("planned_rr"),
        updated_data.get("realized_rr"),
        updated_data.get("profit_percent"),
        updated_data.get("risk_per_trade"),
        updated_data.get("notes"),
        updated_data.get("rights_wrongs"),
        screenshots_json,
        trade_id
    ))

    conn.commit()
    conn.close()

def delete_trade(trade_id):
    """Delete a trade by ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()
