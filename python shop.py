import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# --- DATA INITIALIZATION ---
if 'users' not in st.session_state: st.session_state.users = {"Laika": "Ayush@092025"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'inventory' not in st.session_state: st.session_state.inventory = {}
if 'sales' not in st.session_state: st.session_state.sales = []
if 'vaccines' not in st.session_state: st.session_state.vaccines = []

# --- LOGIN SECTION ---
if not st.session_state.logged_in:
    st.title("🔐 LAIKA PET MART - LOGIN")
    with st.form("login_form"):
        u_input = st.text_input("Username")
        p_input = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u_input in st.session_state.users and st.session_state.users[u_input] == p_input:
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- SIDEBAR MENU ---
st.sidebar.title("🐾 LAIKA PET MART")
menu = st.sidebar.radio("Main Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💉 Vaccine Tracker", "⚙️ Settings"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- VACCINE TRACKER SECTION (Naya Column) ---
if menu == "💉 Vaccine Tracker":
    st.title("Pet Health & Vaccine Record")
    
    # 1. Entry Form
    with st.form("vaccine_form", clear_on_submit=True):
        st.subheader("Nayi Vaccine Entry")
        col1, col2 = st.columns(2)
        with col1:
            owner = st.text_input("Customer Name")
            pet_name = st.text_input("Pet Name (Dog/Cat)")
        with col2:
            v_name = st.text_input("Vaccine Name (e.g. ARV, DHPP)")
            v_date = st.date_input("Aaj ki Tarikh", datetime.now())
            next_date = st.date_input("Agli Vaccine ki Tarikh", datetime.now() + timedelta(days=30))
        
        if st.form_submit_button("Record Save Karein (Enter)"):
            st.session_state.vaccines.append({
                "Customer": owner, "Pet": pet_name, "Vaccine": v_name, 
                "Date Done": v_date, "Next Due": next_date
            })
            st.success(f"✅ {pet_name} ka record save ho gaya!")

    # 2. Display Records
    st.subheader("Purane Records")
    if st.session_state.vaccines:
        v_df = pd.DataFrame(st.session_state.vaccines)
        st.dataframe(v_df, use_container_width=True)
    else:
        st.info("Abhi tak koi vaccine record nahi hai.")

# --- BAKI PURANA CODE (Billing, Stock etc.) ---
elif menu == "📦 Purchase":
    st.title("Stock Entry")
    with st.form("p_form", clear_on_submit=True):
        n = st.text_input("Item Name")
        b = st.number_input("Buy Rate", min_value=0.0)
        s = st.number_input("Sell Rate", min_value=0.0)
        w = st.number_input("Qty/Weight", min_value=0.0)
        if st.form_submit_button("Save (Enter)"):
            st.session_state.inventory[n] = {'p_price': b, 's_price': s, 'qty': w}
            st.success("Saved!")
