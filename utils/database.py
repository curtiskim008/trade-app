import sqlite3
import json
import os
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
        json.dumps(trade_data.get("screenshots", {}))
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


# --- Update a Trade ---
def update_trade(trade_id: int, trade_data: dict):
    """
    Updates a trade and cleans up replaced screenshots.
    Handles both dict and string JSON formats safely.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch existing screenshots
    cursor.execute("SELECT screenshots FROM trades WHERE id = ?", (trade_id,))
    row = cursor.fetchone()
    old_screenshots = {}
    if row and row[0]:
        try:
            old_screenshots = json.loads(row[0])
            if not isinstance(old_screenshots, dict):
                old_screenshots = {}
        except json.JSONDecodeError:
            old_screenshots = {}

    # Get new screenshots (may be dict or JSON string)
    new_screenshots = trade_data.get("screenshots", {})
    if isinstance(new_screenshots, str):
        try:
            new_screenshots = json.loads(new_screenshots)
        except json.JSONDecodeError:
            new_screenshots = {}

    # --- Delete replaced screenshots from disk ---
    for tf, old_path in old_screenshots.items():
        new_path = new_screenshots.get(tf)
        if old_path and os.path.exists(old_path) and new_path != old_path:
            try:
                os.remove(old_path)
            except Exception as e:
                print(f"⚠️ Error removing old screenshot {old_path}: {e}")

    # Update trade record
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
        json.dumps(new_screenshots),
        trade_id
    ))

    conn.commit()
    conn.close()


# --- Delete a Trade and Its Screenshots ---
def delete_trade(trade_id: int):
    """
    Deletes a trade and removes associated screenshots from disk.
    Works with both dict-based and list-based formats.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch screenshots before deleting
    cursor.execute("SELECT screenshots FROM trades WHERE id = ?", (trade_id,))
    row = cursor.fetchone()

    if row and row[0]:
        try:
            screenshots = json.loads(row[0])

            # If dict, delete each image file
            if isinstance(screenshots, dict):
                for path in screenshots.values():
                    if path and os.path.exists(path):
                        os.remove(path)

            # If legacy list format, handle too
            elif isinstance(screenshots, list):
                for path in screenshots:
                    if path and os.path.exists(path):
                        os.remove(path)

        except Exception as e:
            print(f"⚠️ Error deleting screenshots for trade {trade_id}: {e}")

    # Delete record
    cursor.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()
