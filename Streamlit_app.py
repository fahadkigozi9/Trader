import streamlit as st
import pandas as pd
# You can use 'gspread' to connect to your Google Sheet for income tracking

st.title("My Trading Strategy Dashboard")

# 1. Show Strategy Status
st.header("Bot Live Status")
# This will show the status of your strategy
st.write("Strategy: London Momentum Scalper")
st.write("Status: **Active - Monitoring Order Blocks**")

# 2. Show Income Tracker
st.header("Income Tracker")
# Here we connect to the Google Sheet where your bot logs trades
# data = pd.read_csv("your_google_sheet_link_here")
# st.dataframe(data)

# 3. Add a "Quick Trigger" button for your strategy
if st.button("Manually Force Strategy Check"):
    st.write("Checking market conditions...")
    # Your strategy logic goes here
