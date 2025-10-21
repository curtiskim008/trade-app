import sqlite3
import json
from pathlib import Path

# --- Ensure data directory exists ---
data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)
db_path = data_dir / "trades.db"


# --- Initialize Database ---
def init_db():
    """Create the database and the trades table if not exists, and ensure trade_type column exists."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            pair TEXT,
            session TEXT,
            entry_time TEXT,
            exit_time TEXT,
            trade_type TEXT DEFAULT 'Live',
            planned_rr REAL,
            realized_rr REAL,
            profit_percent REAL,
            screenshots TEXT,
            notes TEXT,
            rights_wrongs TEXT
        )
    """)

    # --- Ensure trade_type column exists for older databases ---
    cursor.execute("PRAGMA table_info(trades)")
    columns = [col[1] for col in cursor.fetchall()]
    if "trade_type" not in columns:
        cursor.execute("ALTER TABLE trades ADD COLUMN trade_type TEXT DEFAULT 'Live'")

    conn.commit()
    conn.close()


# --- Insert a New Trade ---
def add_trade(trade_data):
    """
    trade_data: dict with keys
    ['date', 'pair', 'session', 'entry_time', 'exit_time', 'trade_type',
     'planned_rr', 'realized_rr', 'profit_percent', 'screenshots',
     'notes', 'rights_wrongs']
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Convert list of screenshots to JSON
    screenshots_json = json.dumps(trade_data.get("screenshots", []))

    cursor.execute("""
        INSERT INTO trades (
            date, pair, session, entry_time, exit_time, trade_type,
            planned_rr, realized_rr, profit_percent, screenshots,
            notes, rights_wrongs
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_data["date"],
        trade_data["pair"],
        trade_data["session"],
        trade_data["entry_time"],
        trade_data["exit_time"],
        trade_data.get("trade_type", "Live"),
        trade_data["planned_rr"],
        trade_data["realized_rr"],
        trade_data["profit_percent"],
        screenshots_json,
        trade_data["notes"],
        trade_data["rights_wrongs"]
    ))

    conn.commit()
    conn.close()


# --- Fetch All Trades ---
def fetch_all_trades():
    """Return all trades as a list of dicts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades ORDER BY date DESC")
    columns = [col[0] for col in cursor.description]
    trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return trades


# --- Update an Existing Trade ---
def update_trade(trade_id, updated_data):
    """Update trade details by ID."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE trades
        SET pair=?, session=?, date=?, entry_time=?, exit_time=?,
            trade_type=?, planned_rr=?, realized_rr=?, profit_percent=?,
            notes=?, rights_wrongs=?
        WHERE id=?
    """, (
        updated_data["pair"],
        updated_data["session"],
        updated_data["date"],
        updated_data["entry_time"],
        updated_data["exit_time"],
        updated_data.get("trade_type", "Live"),
        updated_data["planned_rr"],
        updated_data["realized_rr"],
        updated_data["profit_percent"],
        updated_data["notes"],
        updated_data["rights_wrongs"],
        trade_id
    ))

    conn.commit()
    conn.close()


# --- Delete a Trade by ID ---
def delete_trade(trade_id):
    """Delete a single trade by ID."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()


# --- Delete All Trades (use carefully) ---
def delete_all_trades():
    """Delete all trades (for reset/testing purposes)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trades")
    conn.commit()
    conn.close()
