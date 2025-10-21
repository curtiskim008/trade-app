# utils/database.py
import os
import json
from sqlalchemy import create_engine, text
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError

# --- DATABASE CONNECTION SETUP ---

# Use SQLite (local database file)
data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)
local_db = data_dir / "trades.db"
DATABASE_URL = f"sqlite:///{local_db}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False, future=True)

# --- DATABASE INITIALIZATION ---
def init_db():
    """Create trades table if it doesn't exist."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        pair TEXT,
        session TEXT,
        entry_time TEXT,
        exit_time TEXT,
        trade_type TEXT,
        planned_rr REAL,
        realized_rr REAL,
        profit_percent REAL,
        screenshots TEXT,
        notes TEXT,
        rights_wrongs TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(create_sql))
        print("✅ Local SQLite database initialized successfully.")
    except SQLAlchemyError as e:
        print("❌ Error initializing local database:", e)


# --- ADD NEW TRADE ---
def add_trade(trade_data: dict):
    """Insert new trade record. Expects keys matching table columns."""
    screenshots_json = json.dumps(trade_data.get("screenshots", []))
    insert_sql = text("""
        INSERT INTO trades (
            date, pair, session, entry_time, exit_time, trade_type,
            planned_rr, realized_rr, profit_percent, screenshots, notes, rights_wrongs
        )
        VALUES (
            :date, :pair, :session, :entry_time, :exit_time, :trade_type,
            :planned_rr, :realized_rr, :profit_percent, :screenshots, :notes, :rights_wrongs
        );
    """)
    params = {
        "date": trade_data.get("date"),
        "pair": trade_data.get("pair"),
        "session": trade_data.get("session"),
        "entry_time": trade_data.get("entry_time"),
        "exit_time": trade_data.get("exit_time"),
        "trade_type": trade_data.get("trade_type", "Live"),
        "planned_rr": trade_data.get("planned_rr"),
        "realized_rr": trade_data.get("realized_rr"),
        "profit_percent": trade_data.get("profit_percent"),
        "screenshots": screenshots_json,
        "notes": trade_data.get("notes"),
        "rights_wrongs": trade_data.get("rights_wrongs"),
    }
    try:
        with engine.begin() as conn:
            conn.execute(insert_sql, params)
            print("✅ Trade added successfully (SQLite).")
            return True
    except SQLAlchemyError as e:
        print("❌ Error adding trade:", e)
        return False


# --- FETCH ALL TRADES ---
def fetch_all_trades():
    """Return all trades as list of dicts, ordered by date desc."""
    select_sql = text("SELECT * FROM trades ORDER BY date DESC, created_at DESC;")
    try:
        with engine.connect() as conn:
            result = conn.execute(select_sql)
            rows = [dict(row) for row in result.mappings().all()]
            for r in rows:
                if r.get("screenshots"):
                    try:
                        r["screenshots"] = json.loads(r["screenshots"])
                    except Exception:
                        r["screenshots"] = []
            return rows
    except SQLAlchemyError as e:
        print("❌ Error fetching trades:", e)
        return []


# --- UPDATE EXISTING TRADE ---
def update_trade(trade_id: int, updated_data: dict):
    """Update trade row by ID."""
    allowed = [
        "date", "pair", "session", "entry_time", "exit_time", "trade_type",
        "planned_rr", "realized_rr", "profit_percent", "screenshots", "notes", "rights_wrongs"
    ]
    set_parts, params = [], {}
    for k, v in updated_data.items():
        if k not in allowed:
            continue
        params[k] = json.dumps(v) if k == "screenshots" else v
        set_parts.append(f"{k} = :{k}")
    if not set_parts:
        return 0
    params["id"] = trade_id
    sql = text(f"UPDATE trades SET {', '.join(set_parts)} WHERE id = :id;")

    try:
        with engine.begin() as conn:
            result = conn.execute(sql, params)
            print(f"✅ Trade {trade_id} updated successfully (SQLite).")
            return result.rowcount
    except SQLAlchemyError as e:
        print("❌ Error updating trade:", e)
        return 0


# --- DELETE TRADE ---
def delete_trade(trade_id: int):
    """Delete trade by ID."""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("DELETE FROM trades WHERE id = :id;"), {"id": trade_id})
            print(f"🗑️ Trade {trade_id} deleted successfully (SQLite).")
            return result.rowcount
    except SQLAlchemyError as e:
        print("❌ Error deleting trade:", e)
        return 0


# --- FETCH TRADE BY ID ---
def fetch_trade_by_id(trade_id: int):
    """Fetch a single trade by ID."""
    try:
        with engine.connect() as conn:
            r = conn.execute(
                text("SELECT * FROM trades WHERE id = :id;"),
                {"id": trade_id}
            ).mappings().first()
            if r:
                row = dict(r)
                if row.get("screenshots"):
                    try:
                        row["screenshots"] = json.loads(row["screenshots"])
                    except Exception:
                        row["screenshots"] = []
                return row
            return None
    except SQLAlchemyError as e:
        print("❌ Error fetching trade by ID:", e)
        return None
