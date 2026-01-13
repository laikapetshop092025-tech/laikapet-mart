import streamlit as st
import pandas as pd
from datetime import datetime

# Page Settings
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_login():
    # Username: Laika | Password: Ayush@092025
    if st.session_state.user_input == "Laika" and st.session_state.pass_input == "Ayush@092025":
        st.session_state.logged_in = True
    else:
        st.error("Galt Username ya Password! Phir se koshish karein.")

if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - SECURE LOGIN")
    st.text_input("Username", key="user_input")
    st.text_input("Password", type="password", key="pass_input")
    st.button("Login", on_click=check_login)
    st.stop()

# --- DATABASE SETUP (After Login) ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'expenses' not in st.session_state: st.session_state.expenses = []
if 'ledger' not in st.session_state: st.session_state.ledger = []

# Sidebar Menu
st.sidebar.title("🐾 LAIKA PET MART")
st.sidebar.success(f"Welcome, Laika Admin")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Stock Entry", "💸 Udhaar Tracker", "💰 Expense Manager", "⚙️ Settings"])

# 1. DASHBOARD
if menu == "📊 Dashboard":
    st.title("Admin Financial Dashboard")
    t_sale = sum(s['total'] for s in st.session_state.sales)
    t_profit = sum(s['profit'] for s in st.session_state.sales)
    t_exp = sum(e['amount'] for e in st.session_state.expenses)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("TOTAL SALES", f"Rs. {t_sale}")
    col2.metric("NET PROFIT", f"Rs. {t_profit - t_exp}")
    col3.metric("EXPENSES", f"Rs. {t_exp}")

# --- Logout Button ---
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Note: Billing, Stock, Udhaar ka pura code aapke purane version wala hi ismein kaam karega.
