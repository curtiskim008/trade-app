import streamlit as st
import pandas as pd
from pathlib import Path
from utils import database as db

st.set_page_config(page_title="⚙️ Settings / Export", layout="wide")
st.title("⚙️ Settings & Data Export")

# Fetch all trades
trades = db.fetch_all_trades()
if not trades:
    st.info("No trades available to export.")
    st.stop()

df = pd.DataFrame(trades)

# Ensure date column is proper datetime
df["date"] = pd.to_datetime(df["date"], errors="coerce")

st.subheader("Download Your Trade Data")

# Export to CSV
csv_data = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download CSV",
    data=csv_data,
    file_name="trades_export.csv",
    mime="text/csv"
)

# Optional: Export to Excel
excel_path = Path("trades_export.xlsx")
df.to_excel(excel_path, index=False)
with open(excel_path, "rb") as f:
    st.download_button(
        label="📥 Download Excel",
        data=f,
        file_name="trades_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.success("Your trade data is ready for download. You can now open it in Google Sheets or Excel.")
