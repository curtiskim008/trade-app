import streamlit as st
from datetime import datetime
from utils import database as db
from pathlib import Path
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="➕ Add New Trade", layout="wide")

# --- Initialize DB ---
db.init_db()

# --- Directories ---
data_dir = Path("data")
screenshot_dir = data_dir / "screenshots"
screenshot_dir.mkdir(parents=True, exist_ok=True)

# --- Custom Styling ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem !important;
            padding-left: 6rem !important;
            padding-right: 6rem !important;
            max-width: 1100px !important;
        }
        .stForm {
            background: #f8f9fa;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
        }
        .stButton>button {
            background-color: #4CAF50 !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.7rem 1.2rem !important;
            font-weight: 600 !important;
            border: none;
            transition: 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #43a047 !important;
            transform: translateY(-2px);
        }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h2 style='text-align:center;'>➕ Log a New Trade</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Record your trade details, screenshots, and reflections in one flow.</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- FORM ---
with st.form("add_trade_form"):
    pair = st.selectbox(
        "Pair",
        ["Select a pair", "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD"]
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        session = st.selectbox("Session", ["London", "New York", "Asian", "Other"])
    with col2:
        date = st.date_input("Date", datetime.today())
    with col3:
        trade_type = st.selectbox("Trade Type", ["Live", "Backtest", "Demo"])

    col4, col5 = st.columns(2)
    with col4:
        entry_time = st.text_input("Entry Time (e.g., 09:30)")
    with col5:
        exit_time = st.text_input("Exit Time (e.g., 10:45)")

    col6, col7, col8, col9 = st.columns(4)
    with col6:
        planned_rr = st.number_input("Planned R:R", value=2.0, step=0.1)
    with col7:
        realized_rr = st.number_input("Realized R:R", value=0.0, step=0.1)
    with col8:
        profit_percent = st.number_input("Profit (%)", value=0.0, step=0.1)
    with col9:
        risk_per_trade = st.number_input("Risk per Trade (%)", value=1.0, step=0.1)

    # --- SCREENSHOTS ---
    st.markdown("#### 📸 Upload Screenshots")
    screenshots = {}
    timeframes = ["daily", "h4", "h1", "m15", "m5", "outcome"]
    for tf in timeframes:
        with st.expander(f"{tf.upper()} Timeframe"):
            file = st.file_uploader(
                f"Upload {tf.upper()} Screenshot",
                type=["png", "jpg", "jpeg"],
                key=f"{tf}_upload"
            )
            screenshots[tf] = file

    # --- NOTES & REFLECTION ---
    notes = st.text_area("Trade Notes / Observations", height=120, placeholder="Describe your setup, emotions, and reasoning.")
    rights_wrongs = st.text_area("Rights & Wrongs (What went well or poorly?)", height=120, placeholder="Reflect on what you did right or could improve next time.")

    submitted = st.form_submit_button("💾 Save Trade")

    if submitted:
        # Save screenshots
        saved_screenshots = {}
        for tf, file in screenshots.items():
            if file:
                save_path = screenshot_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S_')}{tf}_{file.name}"
                with open(save_path, "wb") as f:
                    f.write(file.read())
                saved_screenshots[tf] = str(save_path)
            else:
                saved_screenshots[tf] = None

        trade_data = {
            "pair": pair if pair != "Select a pair" else "",
            "session": session.strip(),
            "date": date.strftime("%Y-%m-%d"),
            "entry_time": entry_time.strip(),
            "exit_time": exit_time.strip(),
            "trade_type": trade_type.strip(),
            "planned_rr": planned_rr,
            "realized_rr": realized_rr,
            "profit_percent": profit_percent,
            "risk_per_trade": risk_per_trade,
            "notes": notes.strip(),
            "rights_wrongs": rights_wrongs.strip(),
            "screenshots": json.dumps(saved_screenshots)
        }

        if pair != "Select a pair" and session:
            db.add_trade(trade_data)
            st.success(f"✅ Trade for {pair} ({trade_type}) added successfully!")
        else:
            st.error("❌ Please select a valid Pair and Session.")
