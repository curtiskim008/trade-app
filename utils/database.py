import os
from sqlalchemy import create_engine, text
import pandas as pd

# ---------------------------
# Database connection
# ---------------------------
# Use environment variable on Streamlit Cloud
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/trades.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)


# ---------------------------
# Initialize the database
# ---------------------------
def init_db():
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with engine.begin() as conn:
        conn.execute(text(create_sql))


# ---------------------------
# Add a new trade
# ---------------------------
def add_trade(trade_data: dict):
    """
    Insert new trade. Expects keys matching columns (date as 'YYYY-MM-DD').
    """
    sql = text("""
        INSERT INTO trades (
            date, pair, session, entry_time, exit_time,
            trade_type, planned_rr, realized_rr, profit_percent,
            screenshots, notes, rights_wrongs
        )
        VALUES (
            :date, :pair, :session, :entry_time, :exit_time,
            :trade_type, :planned_rr, :realized_rr, :profit_percent,
            :screenshots, :notes, :rights_wrongs
        )
    """)
    with engine.begin() as conn:
        conn.execute(sql, trade_data)


# ---------------------------
# Fetch all trades
# ---------------------------
def get_all_trades():
    """
    Return all trades as a pandas DataFrame.
    """
    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM trades ORDER BY date DESC;", conn)
    return df


# ---------------------------
# Filter trades by type (Live / Demo / Backtest)
# ---------------------------
def filter_trades(trade_type=None):
    """
    Return trades filtered by type (if provided).
    """
    query = "SELECT * FROM trades"
    params = {}

    if trade_type and trade_type.lower() != "all":
        query += " WHERE LOWER(trade_type) = :trade_type"
        params["trade_type"] = trade_type.lower()

    query += " ORDER BY date DESC;"

    with engine.begin() as conn:
        df = pd.read_sql(text(query), conn, params=params)
    return df
