import streamlit as st
import pandas as pd
import json
import base64
from datetime import datetime
from utils import database as db

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="📒 Trade Journal")
st.title("📒 Your Trade Journal")

# --- INIT DATABASE ---
db.init_db()

# --- LOAD TRADES ---
trades = db.fetch_all_trades()
if not trades:
    st.info("No trades yet. Add your first one from the ➕ Add Trade page.")
    st.stop()

df = pd.DataFrame(trades)
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# --- FILTERS ---
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        pairs = ["All"] + sorted(df["pair"].dropna().unique().tolist())
        selected_pair = st.selectbox("Pair", pairs)
    with c2:
        sessions = ["All"] + sorted(df["session"].dropna().unique().tolist())
        selected_session = st.selectbox("Session", sessions)
    with c3:
        min_date = df["date"].min().date() if not df["date"].isna().all() else datetime.today().date()
        max_date = df["date"].max().date() if not df["date"].isna().all() else datetime.today().date()
        start_date, end_date = st.date_input("Date Range", (min_date, max_date))
    with c4:
        trade_types = ["All"] + sorted(df["trade_type"].dropna().unique().tolist()) if "trade_type" in df.columns else ["All"]
        selected_type = st.selectbox("Trade Type", trade_types)

# --- APPLY FILTERS ---
filtered = df.copy()
if selected_pair != "All":
    filtered = filtered[filtered["pair"] == selected_pair]
if selected_session != "All":
    filtered = filtered[filtered["session"] == selected_session]
if selected_type != "All":
    filtered = filtered[filtered["trade_type"] == selected_type]

filtered = filtered[(df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)]
if filtered.empty:
    st.warning("No trades match your filters.")
    st.stop()

# --- HELPERS ---
def file_to_base64(uploaded_file):
    if uploaded_file:
        return base64.b64encode(uploaded_file.read()).decode()
    return None

def show_base64_image(img_b64):
    if img_b64:
        st.image(f"data:image/png;base64,{img_b64}", use_container_width=True)
    else:
        st.info("No screenshot uploaded.")

# --- DISPLAY TRADES ---
for _, trade in filtered.sort_values(by="date", ascending=False).iterrows():
    screenshots = {}
    try:
        screenshots = json.loads(trade.get("screenshots", "{}"))
        if not isinstance(screenshots, dict):
            screenshots = {}
    except Exception:
        screenshots = {}

    trade_date = trade["date"].strftime('%Y-%m-%d') if not pd.isna(trade["date"]) else "N/A"
    trade_day = trade["date"].strftime('%A') if not pd.isna(trade["date"]) else "Unknown Day"
    expander_label = f"📘 {trade['pair']} | {trade_day}, {trade_date}"

    with st.expander(expander_label, expanded=False):
        st.markdown(f"💰 Profit: {trade.get('profit_percent','N/A')}% | 🎯 Planned R:R: {trade.get('planned_rr','N/A')} | ✅ Realized R:R: {trade.get('realized_rr','N/A')} | ⚖️ Risk: {trade.get('risk_per_trade','N/A')}% | 📈 Type: {trade.get('trade_type','N/A')}")

        st.markdown("### 🖼️ Screenshots")
        for tf in ["daily", "h4", "h1", "m15", "m5", "outcome"]:
            with st.expander(f"📸 {tf.upper()} Chart", expanded=False):
                show_base64_image(screenshots.get(tf))

        st.markdown("### 🧠 Notes")
        st.write(trade.get("notes", "_No notes provided._"))

        st.markdown("### ⚖️ Rights & Wrongs")
        st.write(trade.get("rights_wrongs", "_No reflections provided._"))

        # --- Edit / Delete Buttons ---
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✏️ Edit Trade {trade['id']}", key=f"edit_{trade['id']}"):
                st.session_state["edit_trade_id"] = trade["id"]
                st.rerun()
        with col2:
            if st.button(f"🗑️ Delete Trade {trade['id']}", key=f"delete_{trade['id']}"):
                db.delete_trade(trade["id"])
                st.success(f"Trade {trade['id']} deleted successfully.")
                st.rerun()
