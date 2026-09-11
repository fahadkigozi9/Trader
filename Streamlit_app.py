import os
import requests
import pandas as pd
import streamlit as st
import yfinance as yf
from google import genai

st.set_page_config(page_title="London Momentum Scalper", layout="wide")

st.title("My Trading Strategy Dashboard")

# ---------------------------------------------------------
# Secrets Synchronization
# ---------------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# ---------------------------------------------------------
# 1. Live Market Data Helper (yfinance)
# ---------------------------------------------------------
@st.cache_data(ttl=300)  # Cache for 5 minutes to protect against yfinance rate limits
def fetch_live_market_data(symbol: str = "GC=F") -> str:
    """
    Fetches real-time 5m price action from Yahoo Finance.
    Symbol 'GC=F' = Gold Futures / Spot XAUUSD proxy.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval="5m")
        
        if df.empty:
            return "Live market data currently unavailable."
            
        recent_df = df.tail(5)
        latest_price = recent_df['Close'].iloc[-1]
        high_5m = recent_df['High'].max()
        low_5m = recent_df['Low'].min()
        
        return (
            f"Asset: XAU/USD (Gold)\n"
            f"Current Price: {latest_price:.2f}\n"
            f"Recent 5m High: {high_5m:.2f}\n"
            f"Recent 5m Low: {low_5m:.2f}\n"
            f"Last Candle Time: {recent_df.index[-1].strftime('%H:%M UTC')}"
        )
    except Exception as e:
        return f"Error fetching live data: {e}"

# ---------------------------------------------------------
# 2. Telegram Alert Dispatcher
# ---------------------------------------------------------
def send_telegram_alert(message: str) -> bool:
    """Pushes a markdown alert to your Telegram via BotFather API."""
    try:
        bot_token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        resp = requests.post(url, data=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        st.error(f"Telegram dispatch failed: {e}")
        return False

# ---------------------------------------------------------
# 3. Bot Live Status
# ---------------------------------------------------------
st.header("Bot Live Status")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Strategy", value="London Momentum Scalper")
with col2:
    st.metric(label="Status", value="Active", delta="Monitoring Order Blocks")
with col3:
    st.metric(label="Primary Asset", value="XAUUSD (Gold)")

st.divider()

# ---------------------------------------------------------
# 4. Income Tracker
# ---------------------------------------------------------
st.header("Income Tracker")

if "trade_history" not in st.session_state:
    st.session_state.trade_history = pd.DataFrame([
        {"Date": "2026-09-08", "Symbol": "XAUUSD", "Type": "BUY", "Lot": 0.10, "Profit/Loss ($)": 45.00},
        {"Date": "2026-09-09", "Symbol": "GBPUSD", "Type": "SELL", "Lot": 0.05, "Profit/Loss ($)": -12.50},
    ])

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
            st.success("Trade recorded!")

df_trades = st.session_state.trade_history
total_pnl = df_trades["Profit/Loss ($)"].sum()
total_trades = len(df_trades)
win_rate = (len(df_trades[df_trades["Profit/Loss ($)"] > 0]) / total_trades * 100) if total_trades > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("Total P&L", f"${total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
m2.metric("Total Trades", total_trades)
m3.metric("Win Rate", f"{win_rate:.1f}%")

st.dataframe(df_trades, use_container_width=True)

st.divider()

# ---------------------------------------------------------
# 5. AI Market Read (Gemini API + Live Data)
# ---------------------------------------------------------
st.header("AI Market Read")

def ask_gemini(user_context: str, live_data: str) -> str:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    prompt = (
        "You're reviewing a London Momentum Scalper order-block setup.\n"
        "Give a short read: bias (long/short/flat), confidence 0-100, "
        "and one risk to watch.\n\n"
        f"--- LIVE MARKET FEED ---\n{live_data}\n\n"
        f"--- USER SETUP DETAILS ---\n{user_context}"
    )
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )
    return response.text

# Fetch live market snapshot
live_market_info = fetch_live_market_data("GC=F")
st.caption(f"**Live Feed:** {live_market_info.replace('\n', ' | ')}")

user_input_context = st.text_area(
    "Order Block Setup Details",
    "e.g. Bullish OB at 2378-2381, London session open, liquidity sweep expected.",
)

auto_alert = st.checkbox("Auto-forward high-confidence signals to Telegram", value=True)

if st.button("Run Gemini Analysis"):
    if not os.environ.get("GEMINI_API_KEY"):
        st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    else:
        try:
            with st.spinner("Analyzing live price action & order block..."):
                analysis_result = ask_gemini(user_input_context, live_market_info)
                st.info(analysis_result)
                
                # Forward to Telegram if enabled
                if auto_alert:
                    if "TELEGRAM_BOT_TOKEN" in st.secrets and "TELEGRAM_CHAT_ID" in st.secrets:

                        alert_msg = f"🚨 *London Scalper Signal Alert* 🚨\n\n{analysis_result}"
                        sent = send_telegram_alert(alert_msg)
                        if sent:
                            st.success("Alert sent to your Telegram!")
                        else:
                            st.warning("Failed to send Telegram alert.")
                    else:
                        st.warning("Telegram secrets missing in `.streamlit/secrets.toml`.")
                        
        except Exception as e:
            st.error(f"Analysis failed: {e}")
