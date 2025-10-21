import streamlit as st
from utils import database as db
from pathlib import Path

# --- Page Config ---
st.set_page_config(
    page_title="Forex Journal App",
    page_icon="💹",
    layout="wide"
)


# --- Main App ---
st.title("💹 Forex Trading Journal")

st.markdown(
    """
    Welcome to your **Forex Journal App** — a place to log, track, and analyze your trades.
    
    Use the sidebar or the navigation bar at the top to:
    - ➕ Add new trades  
    - 📒 View your journaled trades  
    - 📊 Analyze your performance metrics  
    """
)

st.info("👈 Use the left sidebar to navigate through the app pages.")

# --- Optional Footer ---
st.markdown("---")
st.caption("Developed by Hillary Kimutai | Powered by Streamlit")

