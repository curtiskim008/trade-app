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

        /* Text and labels */
        label, .stTextInput, .stSelectbox, .stNumberInput, .stTextArea {
            font-family: 'Inter', sans-serif;
        }

        /* Buttons */
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

        /* Notes and Rights Sections */
        .notes-section {
            background: linear-gradient(135deg, #fff8e1, #fff3c4);
            border-left: 5px solid #ffcc00;
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1rem;
        }
        .rights-section {
            background: linear-gradient(135deg, #e9fdf3, #d2f5e4);
            border-left: 5px solid #00b050;
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1rem;
        }

        .section-label {
            font-weight: 600;
            font-size: 1rem;
            color: #333;
            margin-bottom: 0.3rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h2 style='text-align:center;'>➕ Log a New Trade</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Record your trade details, screenshots, and reflections in one place.</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- TRADE ENTRY FORM ---
with st.form("add_trade_form"):
    # --- BASIC INFO ---
    pair = st.text_input("Pair (e.g., XAUUSD, EURUSD)")
    session = st.selectbox("Session", ["London", "New York", "Asian", "Other"])
    date = st.date_input("Date", datetime.today())
    entry_time = st.text_input("Entry Time (e.g., 09:30)")
    exit_time = st.text_input("Exit Time (e.g., 10:45)")
    trade_type = st.selectbox("Trade Type", ["Live", "Backtest", "Demo"])

    # --- PERFORMANCE METRICS ---
    planned_rr = st.number_input("Planned R:R", value=2.0, step=0.1)
    realized_rr = st.number_input("Realized R:R", value=0.0, step=0.1)
    profit_percent = st.number_input("Profit (%)", value=0.0, step=0.1)

    # --- NOTES SECTION ---
    st.markdown("<div class='notes-section'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>🧠 Trade Notes / Observations</div>", unsafe_allow_html=True)
    notes = st.text_area("", height=120, placeholder="Describe your thought process, setup, emotions, etc.")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- RIGHTS & WRONGS SECTION ---
    st.markdown("<div class='rights-section'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>⚖️ Rights & Wrongs (What went well or poorly?)</div>", unsafe_allow_html=True)
    rights_wrongs = st.text_area("", height=120, placeholder="Reflect on what you did right or could improve next time.")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- SCREENSHOTS ---
    uploaded_files = st.file_uploader(
        "📸 Upload Screenshots (Daily, H4, H1, M15, M5)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    # --- SAVE BUTTON ---
    submitted = st.form_submit_button("💾 Save Trade")

    if submitted:
        screenshot_paths = []
        for file in uploaded_files:
            save_path = screenshot_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S_')}{file.name}"
            with open(save_path, "wb") as f:
                f.write(file.read())
            screenshot_paths.append(str(save_path))

        trade_data = {
            "pair": pair.strip(),
            "session": session.strip(),
            "date": date.strftime("%Y-%m-%d"),
            "entry_time": entry_time.strip(),
            "exit_time": exit_time.strip(),
            "trade_type": trade_type.strip(),
            "planned_rr": planned_rr,
            "realized_rr": realized_rr,
            "profit_percent": profit_percent,
            "notes": notes.strip(),
            "rights_wrongs": rights_wrongs.strip(),
            "screenshots": json.dumps(screenshot_paths)
        }

        if pair and session:
            db.add_trade(trade_data)
            st.success(f"✅ Trade for {pair} ({trade_type}) added successfully!")
        else:
            st.error("❌ Please fill in all required fields (Pair and Session).")
