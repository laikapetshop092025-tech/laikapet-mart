import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# ZAROORI: Yahan apna Step 1 wala Apps Script URL paste karein
SCRIPT_URL = "YAHAN_APNA_APPS_SCRIPT_URL_PASTE_KAREIN" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_to_gsheet(sheet_name, data_list):
    try: requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
    except: st.error("Save nahi ho paya!")

def load_from_gsheet(sheet_name):
    try: return pd.read_csv(SHEET_LINK + sheet_name)
    except: return pd.DataFrame()

# --- 2. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. PURCHASE (Jo yahan bharenge wo Stock mein dikhega) ---
if menu == "📦 Purchase":
    st.header("📦 Purchase / Add Stock")
    inv_df = load_from_gsheet("Inventory")
    with st.form("pur_f"):
        n = st.text_input("Item Name")
        c1, c2 = st.columns(2)
        with c1: q = st.number_input("Qty", min_value=0.1)
        with c2: u = st.selectbox("Unit", ["Pcs", "Kg", "Gm", "Pkt"])
        p = st.number_input("Purchase Price")
        if st.form_submit_button("ADD TO STOCK"):
            save_to_gsheet("Inventory", [n, q, u, p, str(datetime.now().date())])
            st.success("Stock Added!"); st.rerun()
    st.subheader("📋 Purchase History")
    st.table(inv_df.tail(10))

# --- 5. BILLING (Stock se Item uthayega) ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_from_gsheet("Inventory")
    with st.form("bill_f"):
        items = inv_df['Item'].unique().tolist() if not inv_df.empty else ["No Stock"]
        it = st.selectbox("Select Product", items) # Purchase wala item yahan dikhega
        qty = st.number_input("Qty", min_value=0.1)
        pr = st.number_input("Selling Price")
        mode = st.selectbox("Payment", ["Online", "Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            save_to_gsheet("Sales", [str(datetime.now().date()), it, qty, qty*pr, mode])
            st.success("Bill Saved!"); st.rerun()
    st.table(load_from_gsheet("Sales").tail(10))

# --- 6. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    st.table(load_from_gsheet("Inventory"))

# --- 7. BAAKI SECTIONS ---
elif menu == "💰 Expenses":
    e_df = load_from_gsheet("Expenses")
    cat = st.selectbox("Category", ["Rent", "Electricity", "Miscellaneous Expense", "Other"])
    amt = st.number_input("Amount")
    if st.button("Save"):
        save_to_gsheet("Expenses", [str(datetime.now().date()), cat, amt])
        st.success("Saved!"); st.rerun()
    st.table(e_df.tail(10))

elif menu == "🐾 Pet Register":
    breeds = ["Labrador", "German Shepherd", "Pug", "Persian Cat", "Other"]
    with st.form("pet"):
        cn = st.text_input("Customer"); ph = st.text_input("Phone"); br = st.selectbox("Breed", breeds)
        age = st.text_input("Age"); wt = st.text_input("Weight"); vax = st.date_input("Vaccine")
        if st.form_submit_button("SAVE"):
            save_to_gsheet("PetRecords", [cn, ph, br, age, wt, str(vax)])
            st.success("Saved!"); st.rerun()

elif menu == "⚙️ Admin Settings":
    st.subheader("🏢 Company Udhaar (Dues)")
    comp = st.text_input("Company"); amt = st.number_input("Amount")
    if st.button("Save Udhaar"):
        save_to_gsheet("Dues", [comp, amt, str(datetime.now().date())])
        st.success("Saved!"); st.rerun()
    st.subheader("👤 New Staff ID")
    st.text_input("Username"); st.text_input("Password", type="password")
    if st.button("Create ID"): st.success("Created!")
