import streamlit as st
import pandas as pd
import requests # Naya: Data bhejne ke liye
from datetime import datetime

# --- SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")
# Apne Apps Script ka URL yahan dalein
SCRIPT_URL = "AAPKA_WEB_APP_URL_YAHAN_DALEIN" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_data(sheet_name, data_list):
    # Ye function data ko Google Sheet mein bhejega
    requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)

def load_data(sheet_name):
    # Ye function data ko Google Sheet se padhega
    return pd.read_csv(SHEET_LINK + sheet_name)

# --- LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- MENU ---
menu = st.sidebar.radio("Menu", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- BILLING (Pcs/Kg + Online/Offline) ---
if menu == "🧾 Billing":
    st.header("🧾 Billing")
    with st.form("bill"):
        it = st.text_input("Item Name")
        q = st.number_input("Qty", min_value=0.1)
        u = st.selectbox("Unit", ["Pcs", "Kg", "Gm"])
        p = st.number_input("Price", min_value=1)
        mode = st.selectbox("Payment Mode", ["Online", "Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            # Data bhejne ka tareeka
            save_data("Sales", [str(datetime.now().date()), it, f"{q} {u}", q*p, mode])
            st.success("Bill Saved Online!")

# --- PURCHASE (Pcs/Kg) ---
elif menu == "📦 Purchase":
    st.header("📦 Purchase")
    with st.form("pur"):
        n = st.text_input("Item Name")
        q = st.number_input("Qty", min_value=0.1)
        u = st.selectbox("Unit", ["Pcs", "Kg", "Gm"])
        p = st.number_input("Purchase Price")
        if st.form_submit_button("ADD STOCK"):
            save_data("Inventory", [n, q, u, p])
            st.success("Stock Added!")

# --- ADMIN (Udhaar & New ID) ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.subheader("🏢 Company Udhaar")
    c = st.text_input("Company Name")
    a = st.number_input("Amount")
    if st.button("Save Udhaar"):
        save_data("Dues", [c, a])
        st.success("Udhaar Saved!")

# --- PET REGISTER (Full Details) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet"):
        cn = st.text_input("Customer"); ph = st.text_input("Phone")
        br = st.selectbox("Breed", ["Labrador", "German Shepherd", "Other"])
        age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine Date")
        if st.form_submit_button("SAVE"):
            save_data("PetRecords", [cn, ph, br, age, wt, str(vax)])
            st.success("Pet Saved!")
