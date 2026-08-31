import os
import streamlit as st
import pandas as pd
from google import genai
# import MetaTrader5 as mt5  # Uncomment once MT5 terminal is installed and configured

st.title("My Trading Strategy Dashboard")

# 1. Show Strategy Status
st.header("Bot Live Status")
st.write("Strategy: London Momentum Scalper")
st.write("Status: **Active - Monitoring Order Blocks**")

# 2. Show Income Tracker
st.header("Income Tracker")

# 3. AI Market Read (Gemini Free Tier)
st.header("AI Market Read")

def ask_gemini(context: str) -> str:
    # Initialize the Gemini client using the GEMINI_API_KEY environment variable/secrets
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "You're reviewing a London Momentum Scalper order-block setup. "
            "Give a short read: bias (long/short/flat), confidence 0-100, "
            "and one risk to watch. Setup:\n" + context
        ),
    )
    return response.text

# Optional: MT5 Execution Function
def execute_mt5_trade(symbol, lot_size, order_type):
    """
    Connects to MetaTrader 5 and sends a market order.
    Requires MT5 terminal running locally on Windows.
    """
    # if not mt5.initialize():
    #     return f"MT5 initialization failed, error code = {mt5.last_error()}"
    # 
    # point = mt5.symbol_info(symbol).point
    # price = mt5.symbol_info_tick(symbol).ask if order_type == "BUY" else mt5.symbol_info_tick(symbol).bid
    # action = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL
    # 
    # request = {
    #     "action": mt5.TRADE_ACTION_DEAL,
    #     "symbol": symbol,
    #     "volume": lot_size,
    #     "type": action,
    #     "price": price,
    #     "deviation": 20,
    #     "magic": 234000,
    #     "comment": "Streamlit London Scalper",
    #     "type_time": mt5.ORDER_TIME_GTC,
    #     "type_filling": mt5.ORDER_FILLING_IOC,
    # }
    # 
    # result = mt5.order_send(request)
    # mt5.shutdown()
    # return result
    pass

context = st.text_area(
    "Current order block / price context",
    "e.g. Price 2385, bullish OB at 2378-2381, London session open",
)

if st.button("Manually Force Strategy Check"):
    st.write("Checking market conditions...")
    if "GEMINI_API_KEY" not in os.environ:
        st.error("Set GEMINI_API_KEY in your environment/secrets first.")
    else:
        try:
            with st.spinner("Asking Gemini..."):
                analysis_result = ask_gemini(context)
                st.write(analysis_result)
                
                # Example trigger logic (uncomment to test automated MT5 orders based on analysis)
                # if "bias: long" in analysis_result.lower():
                #     trade_res = execute_mt5_trade("XAUUSD", 0.1, "BUY")
                #     st.success(f"MT5 Order Executed: {trade_res}")
                
        except Exception as e:
            st.error(f"Gemini call failed: {e}")
