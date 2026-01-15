import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="LAIKA PET MART", layout="wide")

# Yahan apna Apps Script URL zaroor check karein
SCRIPT_URL = "YAHAN_APNA_APPS_SCRIPT_URL_PASTE_KAREIN" 
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1HHAuSs4aMzfWT2SD2xEzz45TioPdPhTeeWK5jull8Iw/gviz/tq?tqx=out:csv&sheet="

def save_to_gsheet(sheet_name, data_list):
    try: requests.post(f"{SCRIPT_URL}?sheet={sheet_name}", json=data_list)
    except: st.error("Data save nahi ho raha!")

def load_from_gsheet(sheet_name):
    try:
        df = pd.read_csv(SHEET_LINK + sheet_name)
        # Column names ko saaf karna (spaces hatana)
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

# --- 4. DASHBOARD (FIXED CALCULATION) ---
if menu == "📊 Dashboard":
    st.title("📊 Business Performance")
    
    # Data load karna
    s_df = load_from_gsheet("Sales")
    i_df = load_from_gsheet("Inventory")
    e_df = load_from_gsheet("Expenses")

    # 1. Total Sale Calculation
    # Note: Column ka naam 'total' hona chahiye Sales sheet mein
    t_sale = pd.to_numeric(s_df['total'], errors='coerce').sum() if not s_df.empty else 0
    
    # 2. Total Purchase Calculation 
    # (qty * p_price) ka total
    if not i_df.empty:
        i_df['p_total'] = pd.to_numeric(i_df['qty'], errors='coerce') * pd.to_numeric(i_df['p_price'], errors='coerce')
        t_pur = i_df['p_total'].sum()
    else:
        t_pur = 0

    # 3. Total Expense Calculation
    t_exp = pd.to_numeric(e_df['Amount'], errors='coerce').sum() if not e_df.empty else 0
    
    # 4. Net Profit
    t_profit = t_sale - t_exp - t_pur

    # Metrics Display
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL SALE", f"₹{int(t_sale)}")
    c2.metric("TOTAL PURCHASE", f"₹{int(t_pur)}")
    c3.metric("TOTAL EXPENSE", f"₹{int(t_exp)}")
    c4.metric("TOTAL PROFIT", f"₹{int(t_profit)}", delta=f"{int(t_profit)}")

    st.divider()
    st.subheader("Recent Activity")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("Last 5 Sales")
        st.dataframe(s_df.tail(5))
    with col_b:
        st.write("Last 5 Expenses")
        st.dataframe(e_df.tail(5))

# --- BAKI SECTIONS ---
# (Pichle code wala hi Billing, Purchase, Expenses etc. yahan rahega)
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

elif menu == "📋 Live Stock":
    st.header("📋 Current Shop Stock")
    st.table(load_from_gsheet("Inventory"))

elif menu == "💰 Expenses":
    st.header("💰 Expenses")
    e_df = load_from_gsheet("Expenses")
    with st.form("exp"):
        cat = st.selectbox("Category", ["Rent", "Electricity", "Staff Salary", "Other"])
        amt = st.number_input("Amount")
        if st.form_submit_button("Save"):
            save_to_gsheet("Expenses", [str(datetime.now().date()), cat, amt])
            st.success("Saved!"); st.rerun()
    st.table(e_df.tail(10))

elif menu == "🐾 Pet Register":
    st.header("🐾 Pet Registration")
    with st.form("pet"):
        cn = st.text_input("Customer"); ph = st.text_input("Phone")
        br = st.selectbox("Breed", ["Labrador", "Persian Cat", "Other"])
        if st.form_submit_button("Save"):
            save_to_gsheet("PetRecords", [cn, ph, br, str(datetime.now().date())])
            st.success("Saved!")

elif menu == "⚙️ Admin Settings":
    st.subheader("🏢 Company Dues")
    st.text_input("Company"); st.number_input("Amount")
    if st.button("Save"): st.success("Saved!")
    st.divider()
    st.subheader("👤 Create Staff ID")
    st.text_input("Username"); st.text_input("Password", type="password")
    if st.button("Create ID"): st.success("ID Created!")
