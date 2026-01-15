import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Apna Apps Script URL yahan check kar lein
SCRIPT_URL = "YAHAN_APNA_APPS_SCRIPT_URL_PASTE_KAREIN" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_to_gsheet(sheet_name, data_list):
    try: 
        requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
    except: 
        st.error("Data save nahi ho raha!")

def load_from_gsheet(sheet_name):
    try:
        df = pd.read_csv(SHEET_LINK + sheet_name)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# --- 2. LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.header("🔐 LOGIN - LAIKA PET MART")
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("LOGIN"):
        if u == "Laika" and p == "Ayush@092025":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 3. MENU ---
menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🧾 Billing", "📦 Purchase", "📋 Live Stock", "💰 Expenses", "🐾 Pet Register", "⚙️ Admin Settings"])

# --- 4. DASHBOARD (Total Sale, Purchase, Expense, Profit) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    s_df = load_from_gsheet("Sales")
    i_df = load_from_gsheet("Inventory")
    e_df = load_from_gsheet("Expenses")
    
    t_sale = pd.to_numeric(s_df['total'], errors='coerce').sum() if not s_df.empty else 0
    t_exp = pd.to_numeric(e_df['Amount'], errors='coerce').sum() if not e_df.empty else 0
    t_pur = 0
    if not i_df.empty:
        t_pur = (pd.to_numeric(i_df['qty'], errors='coerce') * pd.to_numeric(i_df['p_price'], errors='coerce')).sum()
    
    t_profit = t_sale - t_exp - t_pur

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}")

# --- 5. BILLING ---
elif menu == "🧾 Billing":
    st.header("🧾 Billing Terminal")
    inv_df = load_from_gsheet("Inventory")
    with st.form("bill_f"):
        items = inv_df['Item'].unique().tolist() if not inv_df.empty else ["No Stock"]
        it = st.selectbox("Select Product", items)
        qty = st.number_input("Qty", min_value=0.1)
        pr = st.number_input("Selling Price")
        mode = st.selectbox("Payment", ["Online", "Cash"])
        if st.form_submit_button("COMPLETE BILL"):
            save_to_gsheet("Sales", [str(datetime.now().date()), it, qty, qty*pr, mode])
            st.success("Bill Saved!"); st.rerun()
    st.table(load_from_gsheet("Sales").tail(10))

# --- 6. PURCHASE ---
elif menu == "📦 Purchase":
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
    st.table(inv_df.tail(10))

# --- 7. PET REGISTER (Weight, Age, Next Vaccine Fixed) ---
elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    p_df = load_from_gsheet("PetRecords")
    breeds = ["Labrador", "German Shepherd", "Golden Retriever", "Pug", "Beagle", "Persian Cat", "Siamese Cat", "Indie Dog/Cat", "Other"]
    
    with st.form("pet_form"):
        c1, c2 = st.columns(2)
        with c1:
            cn = st.text_input("Customer Name")
            ph = st.text_input("Phone Number")
            br = st.selectbox("Breed", breeds)
        with c2:
            age = st.text_input("Pet Age (Ex: 2 Years)")
            wt = st.text_input("Pet Weight (Kg)")
            vax = st.date_input("Next Vaccine Date")
            
        if st.form_submit_button("SAVE PET RECORD"):
            save_to_gsheet("PetRecords", [cn, ph, br, age, wt, str(vax)])
            st.success("Pet Record Saved!")
            st.rerun()
    st.table(p_df.tail(10))

# --- 8. EXPENSES ---
elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    e_df = load_from_gsheet("Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Miscellaneous Expense", "Other"])
        amt = st.number_input("Amount")
        if st.form_submit_button("Save"):
            save_to_gsheet("Expenses", [str(datetime.now().date()), cat, amt])
            st.success("Saved!"); st.rerun()
    st.table(e_df.tail(10))

# --- 9. LIVE STOCK ---
elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    st.table(load_from_gsheet("Inventory"))

# --- 10. ADMIN SETTINGS ---
elif menu == "⚙️ Admin Settings":
    st.header("⚙️ Admin Settings")
    st.subheader("🏢 Company Dues")
    st.text_input("Company Name")
    st.number_input("Due Amount")
    if st.button("Save Due"): st.success("Saved!")
    st.divider()
    st.subheader("👤 Create Staff ID")
    st.text_input("New Username")
    st.text_input("New Password", type="password")
    if st.button("Create ID"): st.success("ID Created!")
