import streamlit as st
import pandas as pd
from utils import database as db
import sqlite3
import json
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Trade Journal")
st.title("📒 Your Trade Journal")

# --- Initialize DB ---
db.init_db()

# --- Load Data ---
conn = sqlite3.connect("data/trades.db")
df = pd.read_sql_query("SELECT * FROM trades ORDER BY date DESC", conn)
conn.close()

if df.empty:
    st.info("No trades found yet. Add your first one from the ➕ *Add Trade* page.")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["day"] = df["date"].dt.day_name()

# --- CUSTOM CSS ---
st.markdown("""
<style>
.block-container {padding: 2rem 3rem !important; max-width: 1800px !important;}
.trade-card {border-radius: 16px; padding: 1.5rem; margin-bottom: 2.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: all 0.25s ease;}
.trade-card:hover {transform: scale(1.01); box-shadow: 0 6px 14px rgba(0,0,0,0.15);}
.trade-header {font-size: 1.4rem; font-weight: 700; color: #1e3d59; margin-bottom: 0.3rem;}
.trade-subinfo {font-size: 0.95rem; color: #5f6c7b; margin-bottom: 1rem;}
.section {border-radius: 12px; padding: 1rem 1.5rem; margin-top: 1rem; margin-bottom: 1.2rem; box-shadow: inset 0 0 4px rgba(0,0,0,0.05);}
.details-section { background-color: #f0f7ff; }
.screenshots-section { background-color: #f9f9f9; }
.notes-section { background: linear-gradient(135deg, #fff8e1, #fff3c4); border-left: 5px solid #ffcc00; }
.rights-section { background: linear-gradient(135deg, #e9fdf3, #d2f5e4); border-left: 5px solid #00b050; }
.section-title { font-weight: 700; font-size: 1.1rem; color: #2c3e50; margin-bottom: 0.5rem; }
.profit-positive { background: linear-gradient(135deg, #e6ffe9 0%, #c8f7c5 100%); border-left: 6px solid #00b050; }
.profit-negative { background: linear-gradient(135deg, #ffeaea 0%, #ffc8c8 100%); border-left: 6px solid #d40000; }
.profit-neutral { background: linear-gradient(135deg, #fffde1 0%, #fef5b4 100%); border-left: 6px solid #ffcc00; }
.edit-box { background: #ffffff; border: 1px solid #ddd; border-radius: 12px; padding: 1.5rem; margin-top: 1rem; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.screenshot { border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.stButton>button { border-radius: 8px; padding: 0.4rem 1rem; }
</style>
""", unsafe_allow_html=True)

# --- FILTERS ---
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_pair = st.selectbox("Pair", ["All"] + sorted(df["pair"].unique().tolist()))
    with col2:
        selected_session = st.selectbox("Session", ["All"] + sorted(df["session"].unique().tolist()))
    with col3:
        start_date, end_date = st.date_input("Date Range", value=(df["date"].min(), df["date"].max()))
    with col4:
        trade_types = ["All", "LIVE", "BACKTEST", "DEMO"]
        selected_trade_type = st.selectbox("Trade Type", trade_types)

# --- FILTER LOGIC ---
filtered_df = df.copy()
if selected_pair != "All":
    filtered_df = filtered_df[filtered_df["pair"] == selected_pair]
if selected_session != "All":
    filtered_df = filtered_df[filtered_df["session"] == selected_session]
if selected_trade_type != "All":
    filtered_df = filtered_df[filtered_df["trade_type"].str.upper() == selected_trade_type]
filtered_df = filtered_df[(filtered_df["date"] >= pd.to_datetime(start_date)) & 
                          (filtered_df["date"] <= pd.to_datetime(end_date))]

st.markdown("---")

# --- DISPLAY TRADES ---
for _, row in filtered_df.iterrows():
    profit = float(row["profit_percent"])
    trade_id = row["id"]

    if profit > 0:
        card_class = "profit-positive"
    elif profit < 0:
        card_class = "profit-negative"
    else:
        card_class = "profit-neutral"

    with st.expander(f"📈 {row['pair']} | {row['session']} | {row['date'].strftime('%Y-%m-%d')} ({row['day']}) | {profit}%", expanded=False):
        st.markdown(f"""
            <div class="trade-card {card_class}">
                <div class="trade-header">{row['pair']} — {row['session']} ({row['day']})</div>
                <div class="trade-subinfo">
                    📅 <b>{row['date'].strftime('%Y-%m-%d')}</b> |
                    ⏰ {row['entry_time']} → {row['exit_time']} <br>
                    🎯 Planned R:R: <b>{row['planned_rr']}</b> | Realized R:R: <b>{row['realized_rr']}</b> |
                    💰 Profit: <b>{profit}%</b> | Type: <b>{row.get('trade_type','N/A')}</b>
                </div>
        """, unsafe_allow_html=True)

        # --- SCREENSHOTS SECTION ---
        st.markdown("<div class='section screenshots-section'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>🖼️ Screenshots</div>", unsafe_allow_html=True)
        try:
            screenshots = json.loads(row["screenshots"]) if row["screenshots"] else []
            if screenshots:
                left, right = st.columns(2)
                labels = ["Daily TF", "H4", "H1", "M15", "M5"]
                for i, path in enumerate(screenshots[:5]):
                    col = left if i % 2 == 0 else right
                    with col:
                        st.caption(labels[i] if i < len(labels) else f"Screenshot {i+1}")
                        st.image(path, use_container_width=True)
            else:
                st.caption("_No screenshots available._")
        except Exception:
            st.caption("_No valid screenshots found._")
        st.markdown("</div>", unsafe_allow_html=True)

        # --- NOTES SECTION ---
        st.markdown("<div class='section notes-section'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>🧠 Notes</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='padding-left: 0.5rem;'>{row['notes'] if row['notes'] else '_No notes provided._'}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- RIGHTS/WRONGS SECTION ---
        st.markdown("<div class='section rights-section'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>⚖️ Rights & Wrongs</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='padding-left: 0.5rem;'>{row['rights_wrongs'] if row['rights_wrongs'] else '_No reflection provided._'}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- ACTION BUTTONS ---
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"✏️ Edit Trade {trade_id}", key=f"edit_{trade_id}"):
                st.session_state["edit_trade_id"] = trade_id
        with col2:
            if st.button(f"🗑️ Delete Trade {trade_id}", key=f"delete_{trade_id}"):
                try:
                    conn = sqlite3.connect("data/trades.db")
                    conn.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Trade {trade_id} deleted successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error deleting trade: {e}")

        # --- EDIT FORM BELOW TRADE ---
        if "edit_trade_id" in st.session_state and st.session_state["edit_trade_id"] == trade_id:
            st.markdown("<div class='edit-box'>", unsafe_allow_html=True)
            st.subheader("✏️ Edit Trade")

            pair = st.text_input("Pair", row["pair"], key=f"pair_{trade_id}")
            session = st.text_input("Session", row["session"], key=f"session_{trade_id}")
            date = st.date_input("Date", row["date"].date(), key=f"date_{trade_id}")
            entry_time = st.text_input("Entry Time", row["entry_time"], key=f"entry_{trade_id}")
            exit_time = st.text_input("Exit Time", row["exit_time"], key=f"exit_{trade_id}")
            planned_rr = st.number_input("Planned R:R", value=float(row["planned_rr"]), key=f"prr_{trade_id}")
            realized_rr = st.number_input("Realized R:R", value=float(row["realized_rr"]), key=f"rrr_{trade_id}")
            profit_percent = st.number_input("Profit (%)", value=float(row["profit_percent"]), key=f"profit_{trade_id}")
            notes = st.text_area("Notes", row["notes"], key=f"notes_{trade_id}")
            rights_wrongs = st.text_area("Rights & Wrongs", row["rights_wrongs"], key=f"rw_{trade_id}")

            save_col, cancel_col = st.columns(2)
            with save_col:
                if st.button("💾 Save Changes", key=f"save_{trade_id}"):
                    conn = sqlite3.connect("data/trades.db")
                    conn.execute("""
                        UPDATE trades
                        SET pair=?, session=?, date=?, entry_time=?, exit_time=?,
                            planned_rr=?, realized_rr=?, profit_percent=?, notes=?, rights_wrongs=?
                        WHERE id=?
                    """, (
                        pair, session, date.strftime("%Y-%m-%d"), entry_time, exit_time,
                        planned_rr, realized_rr, profit_percent, notes, rights_wrongs, trade_id
                    ))
                    conn.commit()
                    conn.close()
                    del st.session_state["edit_trade_id"]
                    st.success("✅ Trade updated successfully!")
                    st.rerun()
            with cancel_col:
                if st.button("❌ Cancel", key=f"cancel_{trade_id}"):
                    del st.session_state["edit_trade_id"]
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
