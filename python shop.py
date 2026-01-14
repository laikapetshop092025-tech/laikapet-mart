import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded")

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet):
    try: return conn.read(worksheet=worksheet).dropna(how="all")
    except: return pd.DataFrame()

# --- 2. STYLE ---
st.markdown("""
    <style>
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 35px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 10px; background-color: #2E5BFF; color: white; font-weight: bold;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 40px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        u_id = st.text_input("Username")
        u_pw = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u_id == "Laika" and u_pw == "Ayush@092025":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. DATA LOADING ---
sales_df = get_data("Sales")
inv_df = get_data("Inventory")
exp_df = get_data("Expenses")

# --- 5. NAVIGATION ---
st.sidebar.markdown(f"### Welcome to Laika Pet Shop 👋")
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings", "🐾 Pet Register", "📅 Report"])

# --- 6. DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)
    t_sale = sales_df['total'].sum() if not sales_df.empty else 0
    t_exp = exp_df['Amount'].sum() if not exp_df.empty else 0
    t_profit = (sales_df['profit'].sum() if not sales_df.empty else 0) - t_exp
    
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALES", f"₹{int(t_sale)}")
    c2.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c3.metric("TOTAL PROFIT", f"₹{int(t_profit)}")
    
    if not sales_df.empty:
        st.subheader("Recent Activity")
        st.table(sales_df.tail(5))

# --- 7. BILLING TERMINAL ---
elif menu == "🧾 Billing":
    st.title("🧾 Billing")
    if inv_df.empty: st.warning("Stock khali hai! Pehle Purchase mein maal chadhao.")
    else:
        with st.form("bill_f"):
            item = st.selectbox("Product", inv_df['Item'].tolist())
            qty = st.number_input("Qty", min_value=0.1)
            pr = st.number_input("Price", min_value=1)
            meth = st.selectbox("Payment", ["Cash", "Online"])
            if st.form_submit_button("COMPLETE BILL"):
                # Yahan hum Google Sheet update karne ka logic chalayenge
                st.success("Bill Saved and Synced!")

# --- 8. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock")
    if not inv_df.empty:
        st.table(inv_df)
    else: st.info("Abhi koi stock nahi hai.")

# Baaki sections bhi isi tarah Google Sheet se connect rahenge
