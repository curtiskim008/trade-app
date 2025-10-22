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

# Ensure proper date format
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
else:
    df["date"] = pd.NaT

# --- STYLING ---
st.markdown("""
<style>
    .block-container {padding: 2rem 3rem !important; max-width: 1600px !important;}
    .trade-card {background-color: #ffffff; border-radius: 15px; padding: 1.5rem; margin-bottom: 2rem;
                 box-shadow: 0 4px 12px rgba(0,0,0,0.08);}
    .meta {color: #444; font-size: 0.95rem; margin-bottom: 1rem;}
    .section-header {color: #333; font-size: 1.1rem; font-weight: 600; margin-top: 1rem;}
    .note-box {background-color: #f9f9f9; padding: 1rem; border-radius: 10px;}
    .rw-box {background-color: #f2f2f2; padding: 1rem; border-radius: 10px;}
    .stButton>button {border-radius: 8px; padding: 0.4rem 0.8rem;}
</style>
""", unsafe_allow_html=True)

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

filtered = filtered[
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
]

if filtered.empty:
    st.warning("No trades match your filters.")
    st.stop()

# --- HELPERS ---
def show_base64_image(base64_str):
    if not base64_str:
        st.info("No screenshot uploaded.")
        return
    try:
        image_bytes = base64.b64decode(base64_str)
        st.image(image_bytes, use_container_width=True)
    except Exception:
        st.error("Error displaying image.")

# --- DISPLAY TRADES ---
for _, trade in filtered.sort_values(by="date", ascending=False).iterrows():
    screenshots = {}
    try:
        screenshots = json.loads(trade.get("screenshots", "{}"))
        if not isinstance(screenshots, dict):
            screenshots = {}
    except Exception:
        screenshots = {}

    # --- Expander label ---
    trade_date = trade["date"].strftime('%Y-%m-%d') if not pd.isna(trade["date"]) else "N/A"
    trade_day = trade["date"].strftime('%A') if not pd.isna(trade["date"]) else "Unknown Day"
    expander_label = f"📘 {trade['pair']} | {trade_day}, {trade_date}"

    with st.expander(expander_label, expanded=False):
        st.markdown("<div class='trade-card'>", unsafe_allow_html=True)

        # --- Meta Info ---
        st.markdown(
            f"<div class='meta'>💰 Profit: <b>{trade.get('profit_percent','N/A')}%</b> | "
            f"🎯 Planned R:R: <b>{trade.get('planned_rr','N/A')}</b> | "
            f"✅ Realized R:R: <b>{trade.get('realized_rr','N/A')}</b> | "
            f"⚖️ Risk: <b>{trade.get('risk_per_trade','N/A')}%</b> | "
            f"📈 Type: <b>{trade.get('trade_type','N/A')}</b></div>", unsafe_allow_html=True
        )

        # --- SCREENSHOTS SECTION ---
        st.markdown("<div class='section-header'>🖼️ Screenshots</div>", unsafe_allow_html=True)
        for tf in ["Daily", "H4", "H1", "M15", "M5", "Outcome"]:
            tf_key = tf.lower()
            with st.expander(f"📸 {tf} Chart", expanded=False):
                show_base64_image(screenshots.get(tf_key))

        # --- NOTES SECTION ---
        st.markdown("<div class='section-header'>🧠 Notes</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='note-box'>{trade.get('notes','_No notes provided._')}</div>", unsafe_allow_html=True)

        # --- RIGHTS & WRONGS SECTION ---
        st.markdown("<div class='section-header'>⚖️ Rights & Wrongs</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='rw-box'>{trade.get('rights_wrongs','_No reflections provided._')}</div>", unsafe_allow_html=True)

        # --- ACTION BUTTONS ---
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

        # --- INLINE EDIT FORM ---
        if st.session_state.get("edit_trade_id") == trade["id"]:
            st.divider()
            st.subheader("📝 Edit Trade Details")

            with st.form(f"edit_form_{trade['id']}"):
                updated = {}
                updated["notes"] = st.text_area("Notes", trade.get("notes", ""))
                updated["rights_wrongs"] = st.text_area("Rights & Wrongs", trade.get("rights_wrongs", ""))

                st.markdown("### Update Screenshots")
                new_screenshots = {}
                for tf in ["daily", "h4", "h1", "m15", "m5", "outcome"]:
                    uploaded_file = st.file_uploader(f"Upload {tf.upper()} Screenshot", type=["png","jpg","jpeg"], key=f"{tf}_{trade['id']}")
                    if uploaded_file:
                        new_screenshots[tf] = base64.b64encode(uploaded_file.read()).decode("utf-8")
                    else:
                        new_screenshots[tf] = screenshots.get(tf)

                # Keep other data same
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

        st.markdown("</div>", unsafe_allow_html=True)
