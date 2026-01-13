import streamlit as st
import pandas as pd
from datetime import datetime

# Page Settings
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def check_login():
    if st.session_state.username == "admin" and st.session_state.password == "ayush123": # Aap password yahan badal sakte hain
        st.session_state.logged_in = True
    else:
        st.error("Galt Password! Sahi password dalein.")

if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=check_login)
    st.stop() # Login ke bina aage nahi badhne dega

# --- AGAR LOGIN HO GAYA TOH YE DIKHEGA ---
# Database setup
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'expenses' not in st.session_state: st.session_state.expenses = []

st.sidebar.title("🐾 LAIKA PET MART")
st.sidebar.success(f"Welcome, Admin")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Stock Entry", "💸 Udhaar Tracker", "💰 Expense Manager", "⚙️ Settings"])

# Dashboard Feature
if menu == "📊 Dashboard":
    st.title("Admin Financial Dashboard")
    # ... (Baki purana dashboard code yahan rahega)
    st.write("Ab aapka data safe hai!")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
