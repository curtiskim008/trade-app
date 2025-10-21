import os
import sqlalchemy
from sqlalchemy import create_engine, text
import streamlit as st

# --- Load database URL from Streamlit secrets ---
def get_engine():
    db_url = st.secrets["DATABASE_URL"]
    return create_engine(db_url, pool_pre_ping=True)

# --- Initialize database and table ---
def init_db():
    engine = get_engine()
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
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    with engine.begin() as conn:
        conn.execute(text(create_sql))

# --- Add a new trade ---
def add_trade(trade_data: dict):
    engine = get_engine()
    insert_sql = text("""
        INSERT INTO trades (
            date, pair, session, entry_time, exit_time, trade_type,
            planned_rr, realized_rr, profit_percent, screenshots,
            notes, rights_wrongs
        )
        VALUES (
            :date, :pair, :session, :entry_time, :exit_time, :trade_type,
            :planned_rr, :realized_rr, :profit_percent, :screenshots,
            :notes, :rights_wrongs
        )
    """)
    with engine.begin() as conn:
        conn.execute(insert_sql, trade_data)

# --- Fetch trades ---
def get_all_trades():
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM trades ORDER BY date DESC"))
        rows = result.mappings().all()
    return rows
