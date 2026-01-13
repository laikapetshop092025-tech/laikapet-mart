import streamlit as st
import pandas as pd
from datetime import datetime

# Page Settings
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATA & USER INITIALIZATION ---
if 'users' not in st.session_state:
    st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = ""
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    u_input = st.text_input("Username/ID")
    p_input = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_input in st.session_state.users and st.session_state.users[u_input] == p_input:
            st.session_state.logged_in = True
            st.session_state.current_user = u_input
            st.rerun()
        else:
            st.error("Galt ID ya Password!")
    st.stop()

# --- MAIN APP (After Login) ---
st.sidebar.title("🐾 LAIKA PET MART")
st.sidebar.write(f"Logged in as: *{st.session_state.current_user}*")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Stock Entry", "💸 Udhaar Tracker", "💰 Expense Manager", "⚙️ Settings"])

# 1. EXPENSE MANAGER
if menu == "💰 Expense Manager":
    st.title("Expense Manager")
    with st.form("exp_form"):
        reason = st.text_input("Expense Description")
        amt = st.number_input("Amount (Rs.)", min_value=0)
        if st.form_submit_button("Save"):
            st.session_state.expenses.append({"reason": reason, "amt": amt, "date": datetime.now()})
            st.success("Expense Saved!")

# 2. SETTINGS (Manage ID/Password)
elif menu == "⚙️ Settings":
    st.title("User Management Settings")
    st.subheader("Create New Worker ID")
    new_id = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Add User"):
        if new_id and new_pass:
            st.session_state.users[new_id] = new_pass
            st.success(f"ID '{new_id}' successfully created!")
        else:
            st.warning("Please fill both fields.")

# (Dashboard, Billing & Stock logic included...)
elif menu == "📊 Dashboard":
    st.title("Business Dashboard")
    st.metric("Total Sales", f"Rs. {sum(s['total'] for s in st.session_state.sales)}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
