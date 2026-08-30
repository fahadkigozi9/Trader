import os
import streamlit as st
import pandas as pd
from openai import OpenAI
# You can use 'gspread' to connect to your Google Sheet for income tracking

st.title("My Trading Strategy Dashboard")

# 1. Show Strategy Status
st.header("Bot Live Status")
st.write("Strategy: London Momentum Scalper")
st.write("Status: **Active - Monitoring Order Blocks**")

# 2. Show Income Tracker
st.header("Income Tracker")
# Here we connect to the Google Sheet where your bot logs trades
# data = pd.read_csv("your_google_sheet_link_here")
# st.dataframe(data)

# 3. AI Market Read (DeepSeek) - on-demand advisor call, same pattern as
# the "Ask Claude" button in APEX AI TRADER. Not wired to live execution.
st.header("AI Market Read")


def ask_deepseek(context: str) -> str:
    client = OpenAI(
        api_key=os.environ.get ("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )
    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{
            "role": "user",
            "content": (
                "You're reviewing a London Momentum Scalper order-block setup. "
                "Give a short read: bias (long/short/flat), confidence 0-100, "
                "and one risk to watch. Setup:\n" + context
            ),
        }],
    )
    return resp.choices[0].message.content


# TODO: once this dashboard reads live data (your EA's log, or the Google
# Sheet above), feed that in here automatically instead of typing it by hand.
context = st.text_area(
    "Current order block / price context",
    "e.g. Price 2385, bullish OB at 2378-2381, London session open",
)

if st.button("Manually Force Strategy Check"):
    st.write("Checking market conditions...")
    if "DEEPSEEK_API_KEY" not in os.environ:
        st.error("Set DEEPSEEK_API_KEY in your environment first.")
    else:
        try:
            with st.spinner("Asking DeepSeek..."):
                st.write(ask_deepseek(context))
        except Exception as e:
            st.error(f"DeepSeek call failed: {e}")
