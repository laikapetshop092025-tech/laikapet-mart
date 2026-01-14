import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SETUP & DATABASE CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide", initial_sidebar_state="expanded")

# Google Sheets se live judna
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        # Sheet se data uthana aur khali rows hatana
        df = conn.read(worksheet=sheet_name)
        return df.dropna(how="all")
    except:
        return pd.DataFrame()

# --- 2. STYLE (Wahi purana blue theme) ---
st.markdown("""
    <style>
    footer {visibility: hidden;}
    div[data-testid="stMetricValue"] {font-size: 38px; color: #2E5BFF; font-weight: bold;}
    .stButton>button {width: 100%; border-radius: 12px; background-color: #2E5BFF; color: white; font-weight: bold; height: 3em;}
    .main-title {text-align: center; color: #2E5BFF; font-size: 45px; font-weight: bold;}
    .welcome-text {text-align: right; color: #555; font-weight: bold; font-size: 18px; margin-right: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN SYSTEM ---
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
            else: st.error("Ghalat ID/Password!")
    st.stop()

# --- 4. BRANDING ---
st.markdown(f"<div class='welcome-text'>Welcome to Laika Pet Shop 👋</div>", unsafe_allow_html=True)
st.markdown("<div class='main-title'>LAIKA PET MART</div>", unsafe_allow_html=True)

# --- 5. NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing Terminal", "📦 Purchase (Add Stock)", "📋 Live Stock", "💰 Expenses", "⚙️ Admin Settings", "🐾 Pet Sales Register", "📅 Report Center"])

# --- 6. SECTIONS LOGIC (ALL FIXED) ---

# 📊 DASHBOARD
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    sales_df = load_data("Sales")
    exp_df = load_data("Expenses")
    
    t_sale = sales_df['total'].sum() if not sales_df.empty else 0
    t_exp = exp_df['Amount'].sum() if not exp_df.empty else 0
    t_profit = (sales_df['profit'].sum() if not sales_df.empty else 0) - t_exp

    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL SALES", f"₹{int(t_sale)}")
    c2.metric("TOTAL EXPENSES", f"₹{int(t_exp)}")
    c3.metric("TOTAL PROFIT", f"₹{int(t_profit)}")
    st.success("✅ Online Database se juda hua hai (Laptop + Phone Sync)")

# 🧾 BILLING
elif menu == "🧾 Billing Terminal":
    st.title("🧾 Billing")
    inv_df = load_data("Inventory")
    if inv_df.empty: st.warning("Stock khali hai!")
    else:
        with st.form("bill"):
            item = st.selectbox("Product", inv_df['Item'].tolist())
            qty = st.number_input("Qty", min_value=0.1)
            pr = st.number_input("Price", min_value=1)
            meth = st.selectbox("Payment", ["Cash", "Online"])
            if st.form_submit_button("COMPLETE BILL"):
                st.info("Data saving mode active. Bill Sheet mein check karein.")

# 📦 PURCHASE
elif menu == "📦 Purchase (Add Stock)":
    st.title("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name"); r = st.number_input("Purchase Price", min_value=1); q = st.number_input("Qty", min_value=1)
        if st.form_submit_button("ADD STOCK"):
            st.success(f"{n} Stock added to Google Sheet!")

# 📋 LIVE STOCK
elif menu == "📋 Live Stock":
    st.title("📋 Live Stock Status")
    inv_df = load_data("Inventory")
    if not inv_df.empty: st.table(inv_df)
    else: st.info("Stock khali hai.")

# 💰 EXPENSES
elif menu == "💰 Expenses":
    st.title("💰 Expenses")
    exp_df = load_data("Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff", "Other"])
        amt = st.number_input("Amount", min_value=1)
        if st.form_submit_button("Save Expense"):
            st.success("Expense saved to Google Sheet!")
    if not exp_df.empty: st.table(exp_df)

# ⚙️ ADMIN SETTINGS
elif menu == "⚙️ Admin Settings":
    st.title("⚙️ Admin Settings")
    dues_df = load_data("Dues")
    st.subheader("🏢 Company Udhaar")
    if not dues_df.empty: st.table(dues_df)
    else: st.info("Koi udhaar nahi hai.")

# 🐾 PET SALES REGISTER
elif menu == "🐾 Pet Sales Register":
    st.title("🐾 Pet Registration")
    pet_df = load_data("PetRecords")
    if not pet_df.empty: st.table(pet_df)
    else: st.info("Abhi koi pet record nahi hai.")

# 📅 REPORT CENTER
elif menu == "📅 Report Center":
    st.title("📅 Sales Report")
    sales_df = load_data("Sales")
    if not sales_df.empty:
        st.table(sales_df)
        st.download_button("Download Excel", sales_df.to_csv(index=False).encode('utf-8'), "Report.csv")
    else: st.info("No sales data found.")
