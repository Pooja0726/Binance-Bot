import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

# Ensure the import matches your filename (main.py)
from main import BasicBot

load_dotenv()

st.set_page_config(layout="wide")
st.title("Binance Futures Trading Bot 📈")

# --- Initialization & State Management ---
if 'bot' not in st.session_state:
    st.session_state.bot = None

# --- Sidebar for Connection ---
st.sidebar.header("Connection")
api_key = st.sidebar.text_input("API Key", value=os.getenv('BINANCE_TESTNET_API_KEY', ''))
api_secret = st.sidebar.text_input("API Secret", type="password", value=os.getenv('BINANCE_TESTNET_API_SECRET', ''))

if st.sidebar.button("Connect to Binance"):
    if not api_key or not api_secret:
        st.sidebar.error("Please provide both API Key and Secret.")
    else:
        try:
            with st.spinner("Connecting..."):
                st.session_state.bot = BasicBot(api_key, api_secret, testnet=True)
            st.sidebar.success("✅ Connected successfully!")
        except Exception as e:
            st.sidebar.error(f"Connection failed: {e}")
            st.session_state.bot = None

# --- Main Application Interface ---
if st.session_state.bot:
    bot = st.session_state.bot
    
    with st.expander("📊 Account Balance", expanded=True):
        # (Balance display code is correct)
        try:
            balance_info = bot.get_account_balance()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Margin Balance", f"${balance_info['total_margin_balance']:.2f}")
            col2.metric("Available Balance", f"${balance_info['available_balance']:.2f}")
            pnl = balance_info['total_unrealized_pnl']
            col3.metric("Unrealized PnL", f"${pnl:.2f}", delta=f"{pnl:.2f}")
            st.dataframe(pd.DataFrame(balance_info['balances']))
        except Exception as e:
            st.error(f"Could not retrieve balance: {e}")

    st.markdown("---")
    
    col1, col2 = st.columns(2)

    with col1:
        # (Order placement form is correct)
        st.header("🛒 Place an Order")
        with st.form("order_form"):
            order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
            symbol = st.text_input("Symbol (e.g., BTCUSDT)").upper()
            side = st.selectbox("Side", ["BUY", "SELL"])
            quantity = st.number_input("Quantity", min_value=0.0, format="%.5f")
            price = 0.0
            if order_type == "LIMIT":
                price = st.number_input("Price", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Place Order")
            if submitted:
                try:
                    if order_type == "MARKET":
                        order_result = bot.place_market_order(symbol, side, quantity)
                    else:
                        order_result = bot.place_limit_order(symbol, side, quantity, price)
                    st.success("Order placed successfully!")
                    st.json(order_result)
                except Exception as e:
                    st.error(f"Order failed: {e}")

    with col2:
        st.header("📋 Open Orders")
        if st.button("Refresh Open Orders"):
            try:
                open_orders = bot.get_open_orders()
                st.session_state.open_orders = open_orders
                if not open_orders:
                    st.info("No open orders found.")
            except Exception as e:
                st.error(f"Could not fetch orders: {e}")

        if 'open_orders' in st.session_state and st.session_state.open_orders:
            df_orders = pd.DataFrame(st.session_state.open_orders)
            
            # --- THIS IS THE CORRECTED LINE ---
            # We now use 'order_id' and 'quantity' to match the keys from main.py
            st.dataframe(df_orders[['symbol', 'order_id', 'side', 'type', 'quantity', 'price', 'status']])

            st.subheader("Cancel an Order")
            cancel_id = st.text_input("Order ID to Cancel")
            if st.button("Cancel Order"):
                try:
                    target_order = df_orders[df_orders['order_id'] == int(cancel_id)].iloc[0]
                    with st.spinner(f"Cancelling order {cancel_id}..."):
                        cancel_result = bot.cancel_order(target_order['symbol'], int(cancel_id))
                    st.success(f"Order {cancel_id} cancelled.")
                    st.json(cancel_result)
                    del st.session_state.open_orders # Clear cache to force refresh
                except Exception as e:
                    st.error(f"Failed to cancel order: {e}")
else:
    st.info("Please connect to your Binance Testnet account using the sidebar.")
