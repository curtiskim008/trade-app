# utils/database.py
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from pathlib import Path

# Read DATABASE_URL from environment
DATABASE_URL = os.environ.get("postgresql://postgres:autam28$speed@db.fkucmpsydgobxzdvzbgg.supabase.co:5432/postgres")
if not DATABASE_URL:
    # In local dev you can set this; for safety, we allow a local sqlite fallback only if env missing.
    # But for cloud deployment you must set DATABASE_URL.
    local_db = Path("data") / "trades.db"
    local_db.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{local_db}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False, future=True)

def init_db():
    """Create trades table if it doesn't exist."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS trades (
      id SERIAL PRIMARY KEY,
      date DATE,
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
      created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
    """
    # For SQLite the SERIAL type above will be fine (SQLAlchemy/SQLite accept it), but if you want
    # perfect cross-compatibility you can separate. This works in Postgres.
    with engine.begin() as conn:
        conn.execute(text(create_sql))

def add_trade(trade_data: dict):
    """Insert new trade. Expects keys matching columns (date as 'YYYY-MM-DD')."""
    screenshots_json = json.dumps(trade_data.get("screenshots", []))
    insert_sql = text("""
        INSERT INTO trades (
            date, pair, session, entry_time, exit_time, trade_type,
            planned_rr, realized_rr, profit_percent, screenshots, notes, rights_wrongs
        ) VALUES (
            :date, :pair, :session, :entry_time, :exit_time, :trade_type,
            :planned_rr, :realized_rr, :profit_percent, :screenshots, :notes, :rights_wrongs
        )
        RETURNING id;
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
    with engine.begin() as conn:
        result = conn.execute(insert_sql, params)
        new_id = result.scalar_one()  # returns the id
        return new_id

def fetch_all_trades():
    """Return all trades as a list of dicts, ordered by date desc."""
    select_sql = text("SELECT * FROM trades ORDER BY date DESC, created_at DESC;")
    with engine.connect() as conn:
        result = conn.execute(select_sql)
        rows = [dict(row) for row in result.mappings().all()]
        # Convert screenshots JSON back to list
        for r in rows:
            if r.get("screenshots"):
                try:
                    r["screenshots"] = json.loads(r["screenshots"])
                except Exception:
                    r["screenshots"] = []
        return rows

def update_trade(trade_id: int, updated_data: dict):
    """Update trade row by id. updated_data is a dict of columns to change."""
    # Build SET clause dynamically
    allowed = ["date","pair","session","entry_time","exit_time","trade_type",
               "planned_rr","realized_rr","profit_percent","screenshots","notes","rights_wrongs"]
    set_parts = []
    params = {}
    for k, v in updated_data.items():
        if k not in allowed:
            continue
        if k == "screenshots":
            params[k] = json.dumps(v)
        else:
            params[k] = v
        set_parts.append(f"{k} = :{k}")
    if not set_parts:
        return 0
    params["id"] = trade_id
    sql = text(f"UPDATE trades SET {', '.join(set_parts)} WHERE id = :id;")
    with engine.begin() as conn:
        result = conn.execute(sql, params)
        return result.rowcount

def delete_trade(trade_id: int):
    with engine.begin() as conn:
        result = conn.execute(text("DELETE FROM trades WHERE id = :id;"), {"id": trade_id})
        return result.rowcount

# optional helper
def fetch_trade_by_id(trade_id: int):
    with engine.connect() as conn:
        r = conn.execute(text("SELECT * FROM trades WHERE id = :id;"), {"id": trade_id}).mappings().first()
        if r:
            row = dict(r)
            if row.get("screenshots"):
                try:
                    row["screenshots"] = json.loads(row["screenshots"])
                except Exception:
                    row["screenshots"] = []
            return row
        return None
