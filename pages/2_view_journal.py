import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from utils import database as db

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="📒 Trade Journal")
st.title("📒 Your Trade Journal")

# --- INIT DATABASE ---
db.init_db()

# --- Directories ---
DATA_DIR = Path("data")
SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# --- LOAD TRADES ---
trades = db.fetch_all_trades()
if not trades:
    st.info("No trades yet. Add your first one from the ➕ Add Trade page.")
    st.stop()

df = pd.DataFrame(trades)

# --- DATE FORMATTING ---
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

# --- STYLE ---
st.markdown("""
<style>
.block-container {
    padding: 2rem 3rem !important;
    max-width: 1400px !important;
}
.trade-card {
    background: linear-gradient(to right, #ffffff, #fdfdfd);
    border-radius: 18px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    transition: all 0.2s ease-in-out;
}
.trade-card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    transform: translateY(-3px);
}
.trade-header {
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    padding-bottom: 0.5rem; 
    border-bottom: 1px solid #eee;
}
.trade-meta {
    color: #333;
    font-size: 0.95rem;
    margin-top: 0.8rem;
    line-height: 1.6;
}
.section-title {
    color: #222;
    font-size: 1.05rem;
    font-weight: 600;
    margin-top: 1.4rem;
    margin-bottom: 0.4rem;
}
.note-box, .rw-box {
    background-color: #f8f9fa;
    border: 1px solid #eee;
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    color: #444;
}
.stButton>button {
    border-radius: 8px;
    padding: 0.45rem 0.8rem;
    transition: 0.2s ease-in-out;
}
.stButton>button:hover {
    background-color: #f0f0f0;
}
</style>
""", unsafe_allow_html=True)

# --- FILTERS ---
with st.expander("🔍 Filter Trades", expanded=False):
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

# --- FILTER LOGIC ---
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
def show_image(path):
    """Display an image if it exists; otherwise show message."""
    if not path:
        st.info("No screenshot uploaded.")
        return
    if os.path.exists(path):
        st.image(path, use_container_width=True)
    else:
        st.info("File missing or cannot be displayed.")

def handle_file_upload(label, existing_path=None):
    uploaded_file = st.file_uploader(label, type=["png", "jpg", "jpeg"], key=label)
    if uploaded_file:
        save_path = SCREENSHOT_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(save_path)
    return existing_path

# --- DISPLAY TRADES ---
for _, trade in filtered.sort_values(by="date", ascending=False).iterrows():
    # Safely load screenshots dict
    screenshots = trade.get("screenshots", "{}")
    if isinstance(screenshots, str):
        try:
            screenshots = json.loads(screenshots)
            if not isinstance(screenshots, dict):
                screenshots = {}
        except json.JSONDecodeError:
            screenshots = {}

    trade_date = trade["date"].strftime('%Y-%m-%d') if not pd.isna(trade["date"]) else "N/A"
    trade_day = trade["date"].strftime('%A') if not pd.isna(trade["date"]) else "Unknown Day"
    expander_label = f"📘 {trade['pair']} | {trade_day}, {trade_date}"

    with st.expander(expander_label, expanded=False):
        st.markdown("<div class='trade-card'>", unsafe_allow_html=True)

        # --- HEADER ---
        st.markdown(
            f"""
            <div class='trade-header'>
                <h4 style='margin:0;'>💹 {trade['pair']} | {trade['trade_type'].upper()}</h4>
                <span style='color:#666; font-size:0.9rem;'>Session: {trade.get('session','-')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- META INFO ---
        st.markdown(
            f"""
            <div class='trade-meta'>
            💰 <b>Profit:</b> {trade.get('profit_percent','N/A')}% &nbsp;&nbsp;
            🎯 <b>Planned R:R:</b> {trade.get('planned_rr','N/A')} &nbsp;&nbsp;
            ✅ <b>Realized R:R:</b> {trade.get('realized_rr','N/A')} &nbsp;&nbsp;
            ⚖️ <b>Risk:</b> {trade.get('risk_per_trade','N/A')}% &nbsp;&nbsp;
            🕒 <b>Entry:</b> {trade.get('entry_time','--')} | <b>Exit:</b> {trade.get('exit_time','--')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # --- SCREENSHOTS ---
        st.markdown("<div class='section-title'>🖼️ Trade Screenshots</div>", unsafe_allow_html=True)
        for tf in ["daily", "h4", "h1", "m15", "m5", "outcome"]:
            img_path = screenshots.get(tf)
            with st.expander(f"📸 {tf.upper()} Chart", expanded=False):
                show_image(img_path)

        # --- NOTES ---
        st.markdown("<div class='section-title'>🧠 Trade Notes</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='note-box'>{trade.get('notes','_No notes provided._')}</div>", unsafe_allow_html=True)

        # --- RIGHTS & WRONGS ---
        st.markdown("<div class='section-title'>⚖️ Rights & Wrongs</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='rw-box'>{trade.get('rights_wrongs','_No reflections provided._')}</div>", unsafe_allow_html=True)

        # --- ACTION BUTTONS ---
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✏️ Edit Trade {trade['id']}", key=f"edit_{trade['id']}"):
                st.session_state["edit_trade_id"] = trade["id"]
                st.rerun()
        with col2:
            if st.button(f"🗑️ Delete Trade {trade['id']}", key=f"delete_{trade['id']}", type="secondary"):
                db.delete_trade(trade["id"])
                st.success(f"Trade {trade['id']} deleted successfully.")
                st.rerun()

        # --- INLINE EDIT SECTION ---
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
                    new_screenshots[tf] = handle_file_upload(f"Upload {tf.upper()} Screenshot", screenshots.get(tf))

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
