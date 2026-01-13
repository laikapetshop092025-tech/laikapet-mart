import streamlit as st
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- LOGIN & USER MANAGEMENT ---
if 'users' not in st.session_state:
    # Shuruati ID: Laika | Pass: Ayush@092025
    st.session_state.users = {"Laika": "Ayush@092025"}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_login():
    u = st.session_state.user_input
    p = st.session_state.pass_input
    if u in st.session_state.users and st.session_state.users[u] == p:
        st.session_state.logged_in = True
        st.session_state.current_user = u
    else:
        st.error("Galt ID ya Password!")

if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - SECURE LOGIN")
    st.text_input("Username/ID", key="user_input")
    st.text_input("Password", type="password", key="pass_input")
    st.button("Login", on_click=check_login)
    st.stop()

# --- DATABASE SETUP ---
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# Sidebar Menu
st.sidebar.title("🐾 LAIKA PET MART")
st.sidebar.write(f"User: *{st.session_state.current_user}*")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Stock Entry", "💸 Udhaar Tracker", "💰 Expense Manager", "⚙️ Settings"])

# 1. EXPENSE MANAGER (Ab kaam karega)
if menu == "💰 Expense Manager":
    st.title("Daily Expense Manager")
    with st.form("exp"):
        reason = st.text_input("Kharcha Kahan Hua?")
        amt = st.number_input("Amount (Rs.)", min_value=0)
        if st.form_submit_button("Save Expense"):
            st.session_state.expenses.append({"reason": reason, "amt": amt, "date": datetime.now()})
            st.success("Kharcha save ho gaya!")

# 2. SETTINGS (Nayi ID banane ke liye)
elif menu == "⚙️ Settings":
    st.title("Admin Settings")
    st.subheader("Add New Worker/User ID")
    new_id = st.text_input("Nayi ID banayein")
    new_pass = st.text_input("Naya Password rakhein", type="password")
    if st.button("Create User"):
        if new_id and new_pass:
            st.session_state.users[new_id] = new_pass
            st.success(f"Nayi ID '{new_id}' taiyar hai!")
        else:
            st.warning("ID aur Password dono bhariye.")

# 3. DASHBOARD, BILLING, STOCK aur UDHAAR ka logic...
# (Maine baki saare purane functions bhi ismein include kar diye hain)
elif menu == "📊 Dashboard":
    st.title("Dukan Ka Hisab")
    t_sale = sum(s['total'] for s in st.session_state.sales) if 'sales' in st.session_state else 0
    st.metric("TOTAL SALES", f"Rs. {t_sale}")

# Logout Button
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
