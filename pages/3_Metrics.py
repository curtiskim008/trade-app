import streamlit as st
import pandas as pd
from utils import database as db
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Trading Metrics", layout="wide")
st.markdown("<h1 style='text-align:center;'>📊 Trading Performance Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:18px;'>Analyze your performance across trade types and date ranges</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- Initialize DB ---
db.init_db()

# --- Load Data ---
trades = db.fetch_all_trades()
if not trades:
    st.warning("No trades found. Please log some trades first.")
    st.stop()

df = pd.DataFrame(trades)

# --- Ensure Correct Data Types ---
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["profit_percent"] = pd.to_numeric(df.get("profit_percent", pd.Series()), errors="coerce")
df["realized_rr"] = pd.to_numeric(df.get("realized_rr", pd.Series()), errors="coerce")

# --- FILTERS SECTION ---
st.markdown("### 🔍 Filters")

min_date = df["date"].min().date() if not df["date"].isna().all() else datetime.date.today()
max_date = df["date"].max().date() if not df["date"].isna().all() else datetime.date.today()

filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    start_date = st.date_input("Start Date", value=min_date)
with filter_col2:
    end_date = st.date_input("End Date", value=max_date)
with filter_col3:
    available_types = sorted(df["trade_type"].dropna().astype(str).unique().tolist()) if "trade_type" in df.columns else []
    trade_type = st.selectbox("Trade Type", ["All"] + available_types, index=0)

# --- APPLY FILTERS ---
mask = pd.Series(True, index=df.index)
mask &= df["date"].dt.date.between(start_date, end_date)

if trade_type != "All":
    mask &= df["trade_type"].fillna("").str.lower() == trade_type.lower()

df_filtered = df[mask].copy()

if df_filtered.empty:
    st.warning("No trades match the selected filters.")
    st.stop()

# --- METRICS CALCULATION ---
total_trades = len(df_filtered)
wins = len(df_filtered[df_filtered["profit_percent"] > 0])
losses = len(df_filtered[df_filtered["profit_percent"] < 0])
breakeven = len(df_filtered[df_filtered["profit_percent"] == 0])
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
average_rr = df_filtered["realized_rr"].mean() if not df_filtered["realized_rr"].isna().all() else 0
total_pnl = df_filtered["profit_percent"].sum() if not df_filtered["profit_percent"].isna().all() else 0

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 2.5rem !important;
            padding-bottom: 3rem !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
        }
        .metric-card {
            border-radius: 18px;
            padding: 1.6rem;
            margin-bottom: 1.3rem;
            text-align: center;
            box-shadow: 0px 4px 16px rgba(0,0,0,0.1);
            transition: all 0.25s ease;
            color: white;
            font-family: 'Inter', sans-serif;
        }
        .metric-card:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0px 8px 22px rgba(0,0,0,0.15);
        }
        .total { background: linear-gradient(135deg, #2ecc71, #27ae60); }
        .win { background: linear-gradient(135deg, #3498db, #2980b9); }
        .loss { background: linear-gradient(135deg, #e74c3c, #c0392b); }
        .break { background: linear-gradient(135deg, #f1c40f, #f39c12); }
        .rate { background: linear-gradient(135deg, #9b59b6, #8e44ad); }
        .rr { background: linear-gradient(135deg, #16a085, #1abc9c); }
        .pnl { background: linear-gradient(135deg, #34495e, #2c3e50); }
        .metric-label {
            font-size: 0.95rem;
            font-weight: 500;
            opacity: 0.9;
            margin-bottom: 0.4rem;
            letter-spacing: 0.3px;
        }
        .metric-value {
            font-size: 1.9rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
    </style>
""", unsafe_allow_html=True)

# --- METRICS DISPLAY ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(f"<div class='metric-card total'><div class='metric-label'>Total Trades</div><div class='metric-value'>{total_trades}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card win'><div class='metric-label'>Winning Trades</div><div class='metric-value'>{wins}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card loss'><div class='metric-label'>Losing Trades</div><div class='metric-value'>{losses}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card break'><div class='metric-label'>Break Even Trades</div><div class='metric-value'>{breakeven}</div></div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div class='metric-card rate'><div class='metric-label'>Win Rate (%)</div><div class='metric-value'>{win_rate:.2f}%</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card rr'><div class='metric-label'>Average R:R</div><div class='metric-value'>{average_rr:.2f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-card pnl'><div class='metric-label'>Total PnL (%)</div><div class='metric-value'>{total_pnl:.2f}%</div></div>", unsafe_allow_html=True)
