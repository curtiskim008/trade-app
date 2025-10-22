import streamlit as st
import pandas as pd
import json
from datetime import datetime
from utils import database as db
import base64

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
df["date"] = pd.to_datetime(df.get("date"), errors="coerce")

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
        types = ["All"] + sorted(df["trade_type"].dropna().unique().tolist())
        selected_type = st.selectbox("Trade Type", types)

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
def show_base64_image(base64_str):
    if base64_str:
        st.image(base64.b64decode(base64_str), use_container_width=True)
    else:
        st.info("No screenshot uploaded.")


# --- DISPLAY TRADES ---
for _, trade in filtered.sort_values(by="date", ascending=False).iterrows():
    screenshots = json.loads(trade.get("screenshots") or "{}")
    trade_date = trade["date"].strftime('%Y-%m-%d') if not pd.isna(trade["date"]) else "N/A"
    trade_day = trade["date"].strftime('%A') if not pd.isna(trade["date"]) else "Unknown Day"

    expander_label = f"📘 {trade['pair']} | {trade_day}, {trade_date}"
    with st.expander(expander_label, expanded=False):

        # --- Meta Info ---
        st.markdown(f"💰 Profit: {trade.get('profit_percent','N/A')}% | 🎯 Planned R:R: {trade.get('planned_rr','N/A')} | ✅ Realized R:R: {trade.get('realized_rr','N/A')} | ⚖️ Risk: {trade.get('risk_per_trade','N/A')}% | 📈 Type: {trade.get('trade_type','N/A')}")

        # --- Screenshots ---
        st.markdown("### 🖼️ Screenshots")
        for tf in ["daily","h4","h1","m15","m5","outcome"]:
            with st.expander(f"📸 {tf.upper()} Chart", expanded=False):
                show_base64_image(screenshots.get(tf))

        # --- Notes & Rights/Wrongs ---
        st.markdown("### 🧠 Notes")
        st.write(trade.get("notes") or "_No notes provided._")
        st.markdown("### ⚖️ Rights & Wrongs")
        st.write(trade.get("rights_wrongs") or "_No reflections provided._")

        # --- Actions ---
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

        # --- Inline Edit Form ---
        if st.session_state.get("edit_trade_id") == trade["id"]:
            st.subheader("📝 Edit Trade Details")
            with st.form(f"edit_form_{trade['id']}"):
                updated = {}
                updated["notes"] = st.text_area("Notes", trade.get("notes",""))
                updated["rights_wrongs"] = st.text_area("Rights & Wrongs", trade.get("rights_wrongs",""))

                st.markdown("### Update Screenshots")
                new_screenshots = {}
                for tf in ["daily","h4","h1","m15","m5","outcome"]:
                    uploaded = st.file_uploader(f"{tf.upper()} Screenshot", type=["png","jpg","jpeg"], key=f"upload_{trade['id']}_{tf}")
                    if uploaded:
                        new_screenshots[tf] = base64.b64encode(uploaded.read()).decode("utf-8")
                    else:
                        new_screenshots[tf] = screenshots.get(tf)

                updated.update({
                    "pair": trade.get("pair"),
                    "session": trade.get("session"),
                    "date": trade.get("date").strftime("%Y-%m-%d") if trade.get("date") else "",
                    "entry_time": trade.get("entry_time"),
                    "exit_time": trade.get("exit_time"),
                    "trade_type": trade.get("trade_type"),
                    "planned_rr": trade.get("planned_rr"),
                    "realized_rr": trade.get("realized_rr"),
                    "profit_percent": trade.get("profit_percent"),
                    "risk_per_trade": trade.get("risk_per_trade"),
                    "screenshots": new_screenshots
                })

                submitted = st.form_submit_button("💾 Save Changes")
                if submitted:
                    db.update_trade(trade["id"], updated)
                    st.success("Trade updated successfully.")
                    del st.session_state["edit_trade_id"]
                    st.rerun()
