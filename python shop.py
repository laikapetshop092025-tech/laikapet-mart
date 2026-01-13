import streamlit as st
import pandas as pd
from datetime import datetime

# Page Settings
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_login():
    if st.session_state.user_input == "Laika" and st.session_state.pass_input == "Ayush@092025":
        st.session_state.logged_in = True
    else:
        st.error("Galt Username ya Password!")

if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    st.text_input("Username", key="user_input")
    st.text_input("Password", type="password", key="pass_input")
    st.button("Login", on_click=check_login)
    st.stop()

# --- DATABASE SETUP ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'udhaar' not in st.session_state: st.session_state.udhaar = []

# Sidebar Menu
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Stock Entry", "💸 Udhaar Tracker", "💰 Expense Manager", "⚙️ Settings"])

# 1. DASHBOARD
if menu == "📊 Dashboard":
    st.title("Business Health")
    t_sale = sum(s['total'] for s in st.session_state.sales)
    t_profit = sum(s['profit'] for s in st.session_state.sales)
    t_exp = sum(e['amt'] for e in st.session_state.expenses)
    col1, col2, col3 = st.columns(3)
    col1.metric("SALES", f"Rs. {t_sale}")
    col2.metric("PROFIT", f"Rs. {t_profit - t_exp}")
    col3.metric("EXPENSES", f"Rs. {t_exp}")

# 2. BILLING (Ab kaam karega)
elif menu == "🧾 Billing":
    st.title("Billing Terminal")
    if not st.session_state.inventory:
        st.warning("Pehle Stock Entry mein saaman add karein!")
    else:
        item = st.selectbox("Select Product", list(st.session_state.inventory.keys()))
        qty = st.number_input("Quantity", min_value=1)
        rate = st.number_input("Rate", value=float(st.session_state.inventory[item]['s_price']))
        if st.button("Generate Bill"):
            buy_p = st.session_state.inventory[item]['p_price']
            total = qty * rate
            profit = (rate - buy_p) * qty
            st.session_state.sales.append({"total": total, "profit": profit})
            st.success(f"Bill Saved: Rs. {total}")

# 3. STOCK ENTRY (Ab kaam karega)
elif menu == "📦 Stock Entry":
    st.title("Add New Stock")
    with st.form("stock"):
        name = st.text_input("Item Name")
        buy = st.number_input("Purchase Price")
        sell = st.number_input("Selling Price")
        if st.form_submit_button("Save Item"):
            st.session_state.inventory[name] = {"p_price": buy, "s_price": sell}
            st.success(f"{name} added to Stock!")

# 4. UDHAAR
elif menu == "💸 Udhaar Tracker":
    st.title("Udhaar Register")
    cust = st.text_input("Customer Name")
    amt = st.number_input("Amount")
    if st.button("Save Udhaar"):
        st.session_state.udhaar.append({"name": cust, "amt": amt})
        st.info("Saved!")

# Logout
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
