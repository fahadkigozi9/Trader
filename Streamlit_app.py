import os
import pandas as pd
import streamlit as st
from google import genai

st.set_page_config(page_title="London Momentum Scalper", layout="wide")

st.title("My Trading Strategy Dashboard")

# Ensure GEMINI_API_KEY is available in os.environ from Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# ---------------------------------------------------------
# 1. Show Strategy Status
# ---------------------------------------------------------
st.header("Bot Live Status")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Strategy", value="London Momentum Scalper")
with col2:
    st.metric(label="Status", value="Active", delta="Monitoring Order Blocks")
with col3:
    st.metric(label="Primary Asset", value="XAUUSD / GBPUSD")

st.divider()

# ---------------------------------------------------------
# 2. Show Income Tracker
# ---------------------------------------------------------
st.header("Income Tracker")

# Initialize session state dataframe for trade history if it doesn't exist
if "trade_history" not in st.session_state:
    st.session_state.trade_history = pd.DataFrame(
        [
            {"Date": "2026-09-08", "Symbol": "XAUUSD", "Type": "BUY", "Lot": 0.10, "Profit/Loss ($)": 45.00},
            {"Date": "2026-09-09", "Symbol": "GBPUSD", "Type": "SELL", "Lot": 0.05, "Profit/Loss ($)": -12.50},
        ]
    )

# Form to input new trades
with st.expander("➕ Log a New Trade"):
    with st.form("add_trade_form", clear_on_submit=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            trade_date = st.date_input("Date")
        with f_col2:
            symbol = st.text_input("Symbol", value="XAUUSD").upper()
        with f_col3:
            trade_type = st.selectbox("Type", ["BUY", "SELL"])
        with f_col4:
            pnl = st.number_input("Profit / Loss ($)", value=0.0, step=1.0)
            
        submitted = st.form_submit_button("Record Trade")
        if submitted:
            new_entry = pd.DataFrame([{
                "Date": str(trade_date),
                "Symbol": symbol,
                "Type": trade_type,
                "Lot": 0.10,
                "Profit/Loss ($)": pnl
            }])
            st.session_state.trade_history = pd.concat([st.session_state.trade_history, new_entry], ignore_index=True)
            st.success("Trade recorded successfully!")

# Calculate summary stats
df_trades = st.session_state.trade_history
total_pnl = df_trades["Profit/Loss ($)"].sum()
total_trades = len(df_trades)
win_rate = (len(df_trades[df_trades["Profit/Loss ($)"] > 0]) / total_trades * 100) if total_trades > 0 else 0

m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
m_col2.metric("Total Trades", total_trades)
m_col3.metric("Win Rate", f"{win_rate:.1f}%")

st.dataframe(df_trades, use_container_width=True)

st.divider()

# ---------------------------------------------------------
# 3. AI Market Read (Gemini API)
# ---------------------------------------------------------
st.header("AI Market Read")

def ask_gemini(context: str) -> str:
    # Initialize the client using GEMINI_API_KEY
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-3.5-flash",
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
    if "GEMINI_API_KEY" not in os.environ and "GEMINI_API_KEY" not in st.secrets:
        st.error("Set GEMINI_API_KEY in your environment/secrets first.")
    else:
        try:
            with st.spinner("Asking Gemini..."):
                analysis_result = ask_gemini(context)
                st.info(analysis_result)
                
                # Example trigger logic:
                # if "bias: long" in analysis_result.lower():
                #     trade_res = execute_mt5_trade("XAUUSD", 0.1, "BUY")
                #     st.success(f"MT5 Order Executed: {trade_res}")
                
        except Exception as e:
            st.error(f"Gemini call failed: {e}")
