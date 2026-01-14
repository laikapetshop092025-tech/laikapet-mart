import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. PAGE & DATABASE SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded")

# Google Sheets Se Live Connection
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(sheet_name):
    try:
        # Sheet se data read karna
        return conn.read(worksheet=sheet_name)
    except:
        return pd.DataFrame()

# --- 2. STYLE & LOOK (No Change) ---
st.markdown("""
    <style>
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold;}
    .welcome-text {text-align: right; color: #555; font-weight: bold; font-size: 18px; margin-right: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN (No Change) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.subheader("🔐 Staff Login")
        u_id = st.text_input("Username").strip()
        u_pw = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u_id == "Laika" and u_pw == "Ayush@092025":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. DASHBOARD (LIVE DATA FROM GOOGLE SHEET) ---
st.markdown(f"<div class='welcome-text'>Welcome to Laika Pet Shop 👋</div>", unsafe_allow_html=True)
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)

menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings", "🐾 Pet Sales Register", "📅 Report Center"])

if menu == "📊 Dashboard":
    st.title("📊 Business Performance (Permanent Sync)")
    
    # Live data uthana
    sales_df = get_data("Sales")
    exp_df = get_data("Expenses")
    
    t_sale = sales_df['total'].sum() if not sales_df.empty else 0
    t_exp = exp_df['Amount'].sum() if not exp_df.empty else 0
    # Net Profit = Total Sales Profit - Total Expenses
    t_profit = (sales_df['profit'].sum() if not sales_df.empty else 0) - t_exp

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALES", f"₹{int(t_sale)}")
    c2.metric("TOTAL EXPENSES", f"₹{int(t_exp)}")
    c3.metric("TOTAL PROFIT", f"₹{int(t_profit)}")
    
    st.success("✅ Aapka data ab Google Sheet se juda hai aur Phone-Laptop par hamesha ek jaisa rahega.")

# Note: Baki billing aur inventory ka logic bhi isi tarah conn.update() se kaam karega.
